from app import db

from app.models.reward_point import RewardPoint
from app.models.badge import Badge
from app.models.donor import Donor


# =====================================================
# ADD REWARD POINTS
# =====================================================

def add_reward(donor_id, points, reason):

    donor = Donor.query.get(donor_id)

    if donor is None:
        return None

    reward = RewardPoint(
        donor_id=donor_id,
        points=points,
        reason=reason
    )

    db.session.add(reward)

    # Badge calculation is based on the donor's
    # current donation_count.
    check_badges(donor)

    db.session.commit()

    return reward


# =====================================================
# CHECK AND CREATE DONOR BADGES
# =====================================================

def check_badges(donor):

    donation_count = donor.total_donations or 0

    badge_name = None

    if donation_count >= 20:

        badge_name = "Platinum Donor"

    elif donation_count >= 10:

        badge_name = "Gold Donor"

    elif donation_count >= 5:

        badge_name = "Silver Donor"

    elif donation_count >= 1:

        badge_name = "Bronze Donor"


    if badge_name is None:

        return None


    existing_badge = Badge.query.filter_by(

        donor_id=donor.donor_id,

        badge_name=badge_name

    ).first()


    if existing_badge:

        return existing_badge


    badge = Badge(

        donor_id=donor.donor_id,

        badge_name=badge_name,

        badge_description=f"{badge_name} Achievement",

        badge_icon = f"{badge_name.lower().replace(' ','_')}.png"

    )


    db.session.add(badge)

    return badge


# =====================================================
# GET ALL REWARDS
# =====================================================

def get_rewards(donor_id):

    return RewardPoint.query.filter_by(

        donor_id=donor_id

    ).order_by(

        RewardPoint.created_at.desc()

    ).all()


# =====================================================
# GET TOTAL REWARD POINTS
# =====================================================

def get_total_points(donor_id):

    rewards = RewardPoint.query.filter_by(

        donor_id=donor_id

    ).all()


    return sum(

        reward.points or 0

        for reward in rewards

    )


# =====================================================
# GET ALL BADGES
# =====================================================

def get_badges(donor_id):

    return Badge.query.filter_by(

        donor_id=donor_id

    ).order_by(

        Badge.badge_id.asc()

    ).all()