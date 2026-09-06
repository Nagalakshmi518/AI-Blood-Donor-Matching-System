from app import db
from app.models.hospital import Hospital
from app.notifications.services import create_notification


def create_hospital(data):

    hospital = Hospital(**data)

    db.session.add(hospital)
    db.session.commit()

    return hospital


def get_all_hospitals():

    return Hospital.query.all()


def get_hospital(hospital_id):

    return Hospital.query.get(hospital_id)


def update_hospital(hospital, data):

    for key, value in data.items():
        setattr(hospital, key, value)

    db.session.commit()

    return hospital


def delete_hospital(hospital):

    db.session.delete(hospital)

    db.session.commit()


# ==============================
# Hospital Inventory Services
# ==============================
from app.models.hospital_inventory import HospitalInventory


def get_inventory(hospital_id):
    """Return all inventory records for a hospital."""
    return HospitalInventory.query.filter_by(hospital_id=hospital_id).all()


def _get_inventory_record(hospital_id, blood_group):
    return HospitalInventory.query.filter_by(
        hospital_id=hospital_id, blood_group=blood_group
    ).first()


def add_units(hospital_id, blood_group, units):
    """Add units to hospital inventory. Units must be positive."""
    if units is None or not isinstance(units, int) or units <= 0:
        raise ValueError("Units must be a positive integer")

    inv = _get_inventory_record(hospital_id, blood_group)

    if inv is None:
        # create a new inventory record
        inv = HospitalInventory(
            hospital_id=hospital_id,
            blood_group=blood_group,
            available_units=units,
        )
        db.session.add(inv)
    else:
        inv.available_units = (inv.available_units or 0) + units

    # ensure non-negative
    if inv.available_units < 0:
        raise ValueError("Available units cannot be negative")

    db.session.commit()

    return inv


def use_units(hospital_id, blood_group, units):
    """Use/remove units from hospital inventory. Cannot make available_units negative."""
    if units is None or not isinstance(units, int) or units <= 0:
        raise ValueError("Units must be a positive integer")

    inv = _get_inventory_record(hospital_id, blood_group)

    if inv is None:
        raise ValueError("No inventory record found for this hospital and blood group")

    current = inv.available_units or 0

    if current < units:
        raise ValueError("Insufficient units in inventory")

    inv.available_units = current - units

    # guard again
    if inv.available_units < 0:
        raise ValueError("Available units cannot be negative")

    db.session.commit()

    return inv
# =====================================================
# HOSPITAL INVENTORY FALLBACK FOR NO-DONOR REQUESTS
# =====================================================

def fallback_blood_bank_for_request(blood_request):

    print("\n========== HOSPITAL FALLBACK START ==========")

    if blood_request is None:
        print("Blood request is None")
        return False

    from app.models.patient import Patient
    from app.models.hospital import Hospital
    from app.models.hospital_inventory import HospitalInventory

    required_units = blood_request.units_needed or 1
    blood_group = (blood_request.blood_group or "").strip().upper()

    print("Request ID:", blood_request.request_id)
    print("Blood Group:", blood_group)
    print("Required Units:", required_units)

    # Get patient correctly
    patient = Patient.query.get(blood_request.patient_id)

    # -------------------------------------------------
    # FIND HOSPITAL INVENTORY WITH REQUIRED BLOOD
    # -------------------------------------------------

    
    # -------------------------------------------------
    # HOSPITAL STOCK AVAILABLE
    # -------------------------------------------------
    inventory_records = (
    HospitalInventory.query
    .join(
        Hospital,
        HospitalInventory.hospital_id == Hospital.hospital_id
    )
    .filter(
        db.func.upper(HospitalInventory.blood_group) == blood_group,
        HospitalInventory.available_units >= required_units,
        Hospital.user_id.isnot(None),
        Hospital.is_active.is_(True)
    )
    .order_by(HospitalInventory.available_units.desc())
    .all()
)
    print("Eligible hospitals found:", len(inventory_records))
    if inventory_records:

        selected_inventory = inventory_records[0]

        selected_hospital = Hospital.query.get(
            selected_inventory.hospital_id
        )

        # Reduce blood units
        selected_inventory.available_units = (
            selected_inventory.available_units - required_units
        )

        # Safety check
        if selected_inventory.available_units < 0:
            selected_inventory.available_units = 0

        # Mark request completed
        blood_request.status = "Completed"
        blood_request.fulfillment_source = "HOSPITAL_INVENTORY"

        print(
            f"Blood allocated from Hospital ID: "
            f"{selected_inventory.hospital_id}"
        )

        print(
            f"Remaining units: "
            f"{selected_inventory.available_units}"
        )

        # -------------------------------------------------
        # NOTIFY PATIENT
        # -------------------------------------------------

        if patient and patient.user_id:

            hospital_name = (
                selected_hospital.hospital_name
                if selected_hospital
                else "Hospital"
            )

            create_notification({
                "user_id": patient.user_id,
                "title": "Blood Available in Hospital",
                "message": (
                    f"No eligible donor was available. "
                    f"{required_units} unit(s) of {blood_group} blood "
                    f"were allocated from {hospital_name}."
                ),
                "notification_type": "SUCCESS",
                "related_request_id": blood_request.request_id,
                "is_read": False
            })

        # -------------------------------------------------
        # NOTIFY SELECTED HOSPITAL
        # -------------------------------------------------

        if selected_hospital and selected_hospital.user_id:
            print("Selected Hospital:", selected_hospital.hospital_name)
            print("Hospital User ID:", selected_hospital.user_id)
            print("Creating hospital notification...")

            create_notification({
                "user_id": selected_hospital.user_id,

                "title": "New Blood Request Fulfilled",

                "message": (
                    f"A patient blood request (Request "
                    f"#{blood_request.request_id}) required "
                    f"{required_units} unit(s) of {blood_group} blood. "
                    f"No eligible donor was available, so the request "
                    f"was fulfilled using your hospital inventory. "
                    f"Remaining {blood_group} stock: "
                    f"{selected_inventory.available_units} unit(s)."
                ),

                "notification_type": "INFO",

                "related_request_id": blood_request.request_id,

                "is_read": False
            })
        print("Hospital notification creation attempted")
        db.session.commit()

        print(f"Blood from hospital inventory allocated successfully")
        print("========== HOSPITAL FALLBACK END ==========\n")

        return True

    # -------------------------------------------------
    # NO HOSPITAL STOCK AVAILABLE
    # -------------------------------------------------

    blood_request.status = "Pending"

    if patient and patient.user_id:

        create_notification({
            "user_id": patient.user_id,
            "title": "Blood Currently Unavailable",
            "message": (
                f"No eligible donor or hospital inventory is "
                f"currently available for {blood_group} blood. "
                f"Your request remains active."
            ),
            "notification_type": "WARNING",
            "related_request_id": blood_request.request_id,
            "is_read": False
        })

    db.session.commit()

    print("No donor or hospital inventory available")
    print("========== HOSPITAL FALLBACK END ==========\n")

    return False