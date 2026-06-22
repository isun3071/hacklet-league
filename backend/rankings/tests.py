import pytest
from django.contrib.auth import get_user_model

from rankings.models import Ranking

User = get_user_model()


@pytest.mark.django_db
def test_create_ranking():
    user = User.objects.create_user(email="r@example.com", password="pw")
    ranking = Ranking.objects.create(
        user=user, scope="chapter", period="all_time", rank=1, rank_points=100,
    )
    assert ranking.rank == 1
    assert user.rankings.count() == 1
