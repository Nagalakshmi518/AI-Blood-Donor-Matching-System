from app import db
from app.models.response_history import ResponseHistory


def create_history(data):

    history = ResponseHistory(**data)

    db.session.add(history)
    db.session.commit()

    return history


def get_all_history():

    return ResponseHistory.query.all()


def get_history(history_id):

    return ResponseHistory.query.get(history_id)


def get_history_by_donor(donor_id):

    return ResponseHistory.query.filter_by(
        donor_id=donor_id
    ).all()


def get_history_by_request(request_id):

    return ResponseHistory.query.filter_by(
        request_id=request_id
    ).all()


def update_history(history, data):

    for key, value in data.items():
        setattr(history, key, value)

    db.session.commit()

    return history


def delete_history(history):

    db.session.delete(history)

    db.session.commit()