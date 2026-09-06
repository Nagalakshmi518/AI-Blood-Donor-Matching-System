def predict_response_time(donor):

    if donor.reliability_score >= 9:
        return "5-10 Minutes"

    elif donor.reliability_score >= 7:
        return "10-20 Minutes"

    elif donor.reliability_score >= 5:
        return "20-30 Minutes"

    return "30+ Minutes"