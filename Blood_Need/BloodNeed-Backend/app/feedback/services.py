from app import db
from app.models.feedback import Feedback
from app.models.donor import Donor


def create_feedback(data):

    feedback = Feedback(**data)

    db.session.add(feedback)
    db.session.commit()

    # Update donor reliability score
    donor = Donor.query.get(feedback.donor_id)

    if donor:

        if feedback.rating == 5:
            donor.reliability_score += 2

        elif feedback.rating == 4:
            donor.reliability_score += 1

        elif feedback.rating == 2:
            donor.reliability_score -= 1

        elif feedback.rating == 1:
            donor.reliability_score -= 2

        # Keep score within limits
        if donor.reliability_score < 0:
            donor.reliability_score = 0

        if donor.reliability_score > 100:
            donor.reliability_score = 100

        db.session.commit()

    return feedback


def get_all_feedback():

    return Feedback.query.all()


def get_feedback(feedback_id):

    return Feedback.query.get(feedback_id)


def get_feedback_by_donor(donor_id):

    return Feedback.query.filter_by(
        donor_id=donor_id
    ).all()


def get_feedback_by_patient(patient_id):

    return Feedback.query.filter_by(
        patient_id=patient_id
    ).all()


def update_feedback(feedback, data):

    for key, value in data.items():
        setattr(feedback, key, value)

    db.session.commit()

    return feedback


def delete_feedback(feedback):

    db.session.delete(feedback)
    db.session.commit()


def calculate_average_rating(donor_id):

    feedbacks = Feedback.query.filter_by(
        donor_id=donor_id
    ).all()

    if len(feedbacks) == 0:
        return 0

    total = sum(
        feedback.rating
        for feedback in feedbacks
    )

    return round(
        total / len(feedbacks),
        2
    )