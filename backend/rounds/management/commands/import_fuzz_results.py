"""Import fuzz grade records into the platform (the manual-bridge grading path).

The fuzz runner (`fuzz-runner/`, a separate isolated service) grades each submission and appends
a JSONL grade record via its `--out` flag. This command reads that file, matches each record to
its Submission, writes the authoritative `slop_score`, and stores the itemized findings as
FuzzResult rows. It is the platform half of the platform<->runner contract (FUZZ_RUNNER_SPEC);
the platform never runs submission code itself.

Match key: each record's `repo` field (its basename) is the Submission UUID. Run the runner with
each submission unpacked to a directory named by its submission id, so `repo` -> Submission.pk.

Grade record shape (from the runner's `_grade_record`):
    {"repo", "deployed", "slop_score", "axis_slop", "coverage", "observed_surface",
     "platform", "findings": [{"probe_id","bundle","category","outcome","penalty",...}]}

Re-running is idempotent: a submission's FuzzResults are rebuilt from the latest record.
"""
import json
import os
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from rounds.models import FuzzResult, Submission


def _submission_id(record):
    """The Submission UUID a record refers to: the basename of its `repo`, parsed as a UUID."""
    repo = (record.get("repo") or "").rstrip("/")
    base = os.path.basename(repo) or repo
    try:
        return uuid.UUID(base)
    except (ValueError, AttributeError):
        return None


class Command(BaseCommand):
    help = "Import fuzz runner grade records (JSONL) and write slop scores + findings."

    def add_arguments(self, parser):
        parser.add_argument("file", help="Path to the runner's --out JSONL grade file.")
        parser.add_argument(
            "--round", dest="round_id", default=None,
            help="Optional: only import records whose submission is in this round id.",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Parse and report, write nothing.",
        )

    def handle(self, *args, **opts):
        path = opts["file"]
        if not os.path.exists(path):
            raise CommandError(f"No such file: {path}")

        matched = skipped = findings_written = failed = 0
        with open(path) as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    self.stderr.write(f"  line {lineno}: bad JSON ({e}); skipped")
                    skipped += 1
                    continue

                sub_id = _submission_id(record)
                if sub_id is None:
                    self.stderr.write(
                        f"  line {lineno}: repo {record.get('repo')!r} is not a submission id; skipped"
                    )
                    skipped += 1
                    continue

                sub = (
                    Submission.objects.select_related("round")
                    .filter(pk=sub_id)
                    .first()
                )
                if sub is None:
                    self.stderr.write(f"  line {lineno}: no submission {sub_id}; skipped")
                    skipped += 1
                    continue
                if opts["round_id"] and str(sub.round_id) != opts["round_id"]:
                    skipped += 1
                    continue

                # A record with no slop_score, or deployed=false, is a submission that did not
                # come up as an HTTP service: deploy-failed. It carries no objective score and
                # ranks below every deployed submission (format_spec §5.6).
                deployed = record.get("deployed", True) and "slop_score" in record
                n = self._apply(sub, record, deployed, opts["dry_run"])
                if deployed:
                    matched += 1
                    findings_written += n
                else:
                    failed += 1

        verb = "would import" if opts["dry_run"] else "imported"
        self.stdout.write(
            f"{verb}: {matched} graded ({findings_written} findings), "
            f"{failed} deploy-failed, {skipped} skipped."
        )

    def _apply(self, sub, record, deployed, dry_run):
        """Write one record to its submission. Returns the number of findings written."""
        if dry_run:
            return len([f for f in record.get("findings", []) if deployed])

        with transaction.atomic():
            if not deployed:
                sub.slop_score = None
                sub.status = Submission.Status.SUBMITTED_FAILED
                sub.save(update_fields=["slop_score", "status"])
                return 0

            sub.slop_score = int(record["slop_score"])
            sub.status = Submission.Status.SUBMITTED_DEPLOYED
            sub.save(update_fields=["slop_score", "status"])

            # Rebuild findings from scratch so a re-import is clean (no stale rows).
            sub.fuzz_results.all().delete()
            now = timezone.now()
            rows = []
            for f in record.get("findings", []):
                rows.append(FuzzResult(
                    submission=sub,
                    probe_id=f.get("probe_id", "")[:100],
                    bundle=(f.get("bundle") or "")[:20],
                    category=(f.get("category") or "")[:80],
                    outcome=f.get("outcome") or FuzzResult.Outcome.SLOP_DETECTED,
                    penalty_contributed=max(0, int(f.get("penalty", 0))),
                    evidence={
                        k: f[k] for k in ("reason", "target", "variant_group_id", "evidence")
                        if k in f
                    },
                    ran_at=now,
                ))
            FuzzResult.objects.bulk_create(rows)
            return len(rows)
