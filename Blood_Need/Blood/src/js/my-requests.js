const API_URL = "https://ai-blood-donor-matching-system.onrender.com";
const token = localStorage.getItem("token");

const requestsContainer = document.getElementById("requestsContainer");
async function checkHospitalInventory(requestId) {
  try {
    const response = await fetch(
      `${API_URL}/api/requests/${requestId}/inventory`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    if (!response.ok) {
      console.log("Inventory API status:", response.status);
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Hospital inventory error:", error);
    return null;
  }
}
// =====================================================
// LOAD MY BLOOD REQUESTS
// =====================================================

async function loadMyRequests() {
  if (!token) {
    window.location.href = "login.html";

    return;
  }

  requestsContainer.innerHTML = `

    <p class="loading">

      Loading your blood requests...

    </p>

  `;

  try {
    const response = await fetch(
      `${API_URL}/api/requests/`,

      {
        method: "GET",

        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    let data = {};

    try {
      data = await response.json();
    } catch (parseError) {
      console.error("My Requests JSON parse error:", parseError);
    }

    if (!response.ok) {
      const errorMessage =
        data.message || data.error || data.detail || "Failed to load requests";

      requestsContainer.innerHTML = `

        <p class="empty">

          ${errorMessage}

        </p>

      `;

      return;
    }

    if (!data || data.length === 0) {
      requestsContainer.innerHTML = `

        <p class="empty">

          No blood requests found.

        </p>

      `;

      return;
    }

    requestsContainer.innerHTML = "";

    data.forEach((bloodRequest) => {
      console.log("Blood Request:", bloodRequest);
      console.log("Matched Donors:", bloodRequest.matched_donors);
      const card = document.createElement("div");

      card.className = "request-card";

      const donors = bloodRequest.matched_donors || [];
      const acceptedMatch = donors.find(
        (match) => match.donor_response === "Accepted",
      );
      const showDonationCompletedButton =
        bloodRequest.status === "Accepted" &&
        !acceptedMatch?.donor?.is_completed;

      const validDonors = donors.filter((match) => {
        const donor = match.donor || {};
        return (
          donor.latitude !== null &&
          donor.latitude !== undefined &&
          donor.longitude !== null &&
          donor.longitude !== undefined &&
          !isNaN(parseFloat(donor.latitude)) &&
          !isNaN(parseFloat(donor.longitude))
        );
      });
      const hospitalLat = bloodRequest.hospital_latitude;
      const hospitalLng = bloodRequest.hospital_longitude;

      // =================================================
      // DONOR CARDS
      // =================================================

      const donorsHTML =
        donors.length > 0
          ? donors

              .map((match) => {
                const donor = match.donor || {};

                const donorResponse = match.donor_response || "Pending";

                const donorName = donor.full_name || "Anonymous Donor";
                const donorPhone = donor.phone || "Not Available";
                const donorEmail = donor.email || "Not Available";

                const distance =
                  match.distance_km != null
                    ? `${Number(match.distance_km).toFixed(2)} km`
                    : "Unavailable";

                const rankingScore =
                  match.ranking_score != null
                    ? Number(match.ranking_score).toFixed(2)
                    : "N/A";

                const responseProbability =
                  match.response_probability != null
                    ? `${match.response_probability}%`
                    : "N/A";

                const hasLocation =
                  donor.latitude != null && donor.longitude != null;

                return `

                    <div class="donor-card">


                      <div class="donor-card-header">


                        <h4>

                          🩸 ${donorName}

                        </h4>


                        <span

                          class="response-status

                          ${getResponseClass(donorResponse)}"

                        >

                          ${donorResponse}

                        </span>


                      </div>


                      <div class="donor-details">


                        <p>

                          <strong>

                            Blood Group

                          </strong>


                          <span>

                            ${donor.blood_group || "N/A"}

                          </span>

                        </p>

                        <p>
                          <strong>Phone</strong>
                          <span>${donorPhone}</span>
                        </p>

                        <p>
                          <strong>Email</strong>
                          <span>${donorEmail}</span>
                        </p>


                        <p>

                          <strong>

                            Distance

                          </strong>


                          <span>

                            ${distance}

                          </span>

                        </p>


                        <p>

                          <strong>

                            Ranking Score

                          </strong>


                          <span>

                            ${rankingScore}

                          </span>

                        </p>


                        <p>

                          <strong>

                            Response Probability

                          </strong>


                          <span>

                            ${responseProbability}

                          </span>

                        </p>


                      </div>


                      ${
                        hasLocation
                          ? `

                    <button
class="view-all-map-button"
onclick="viewAllDonorsOnMap(
${bloodRequest.request_id},
${bloodRequest.hospital_latitude},
${bloodRequest.hospital_longitude}
)"
>
🗺️ View All on Map
</button>
                          `
                          : `

                            <p

                              class="location-unavailable"

                            >

                              📍 Location unavailable

                            </p>

                          `
                      }


                    </div>

                  `;
              })

              .join("")
          : `

              <p class="no-donors">

                No matched donors yet.

              </p>

            `;
      // =================================================
      // HOSPITAL INVENTORY FALLBACK
      // =================================================

      const fulfillmentSource = String(
        bloodRequest.fulfillment_source || "",
      ).toUpperCase();

      const inventoryUsed = fulfillmentSource === "HOSPITAL_INVENTORY";

      const inventory = bloodRequest.hospital_inventory || {};

      function renderInventorySection() {
        // Hospital inventory successfully used
        if (inventoryUsed) {
          return `
      <div class="hospital-inventory-card inventory-success">

        <div class="inventory-header">
          <h3>🏥 Hospital Blood Inventory</h3>
        </div>

        <div class="inventory-status">
          🟢 Request Completed via Hospital Inventory
        </div>

        <div class="inventory-message">
          No eligible donor was available. This blood request
          was successfully fulfilled using hospital blood inventory.
        </div>

        <div class="inventory-units">

          <div class="inventory-unit-box">
            <strong>Blood Group</strong>
            <span>${bloodRequest.blood_group}</span>
          </div>

          <div class="inventory-unit-box">
            <strong>Units Used</strong>
            <span>${bloodRequest.units_needed || 1} unit(s)</span>
          </div>

        </div>

      </div>
    `;
        }

        return "";
      }

      let inventoryHTML = renderInventorySection();
      // =================================================
      // REQUEST CARD
      // =================================================

      card.innerHTML = `


        <div class="request-card-header">


          <div>


            <h3>

              Request #${bloodRequest.request_id}

            </h3>


            <span

              class="request-status

              ${getStatusClass(bloodRequest.status)}"

            >

              ${bloodRequest.status}

            </span>

${
  fulfillmentSource === "HOSPITAL_INVENTORY"
    ? `
      <span class="fulfillment-source">
        🏥 Completed via Hospital Inventory
      </span>
    `
    : fulfillmentSource === "DONOR"
      ? `
        <span class="fulfillment-source">
          🩸 Completed via Donor
        </span>
      `
      : ""
}
          </div>


          <span class="request-date">

            ${bloodRequest.request_time || "N/A"}

          </span>


        </div>


        <div class="request-details">


          <div>

            <strong>

              Blood Group

            </strong>


            <span>

              ${bloodRequest.blood_group}

            </span>

          </div>


          <div>

            <strong>

              Units Needed

            </strong>


            <span>

              ${bloodRequest.units_needed}

            </span>

          </div>


          <div>

            <strong>

              Emergency Level

            </strong>


            <span>

              ${bloodRequest.emergency_level}

            </span>

          </div>


<div>

    <strong>Hospital</strong>

    <span>${bloodRequest.hospital_name}</span>

</div>

<div>

    <strong>Location</strong>

    <span>

        ${bloodRequest.hospital_name}

        <br>

        (${bloodRequest.hospital_latitude},
        ${bloodRequest.hospital_longitude})

    </span>

</div>


        </div>


        <div class="matched-donors">


          <div class="matched-donors-header">


            <h3>

              Matched Donors

            </h3>


            ${
              validDonors.length > 0
                ? `

                  <button

                    class="view-all-map-button"

                    onclick="viewAllDonorsOnMap(

                      ${bloodRequest.request_id}

                    )"

                  >

                    🗺️ View All on Map

                  </button>

                `
                : ""
            }


          </div>


          ${donorsHTML}


        </div>

${inventoryHTML}
        ${
          bloodRequest.status === "Pending"
            ? `

              <button

                class="cancel-button"

                onclick="cancelRequest(

                  ${bloodRequest.request_id}

                )"

              >

                Cancel Request

              </button>

            `
            : ""
        }

        ${
          showDonationCompletedButton
            ? `

              <button

                class="cancel-button"

                onclick="completeDonation(

                  ${bloodRequest.request_id}

                )"

              >

                Donation Completed

              </button>

            `
            : ""
        }


      `;

      requestsContainer.appendChild(card);
    });
  } catch (error) {
    console.error(
      "My Requests Error:",

      error,
    );

    requestsContainer.innerHTML = `

      <p class="empty">

        Unable to connect to backend.

      </p>

    `;
  }
}

// =====================================================
// VIEW ALL DONORS ON MAP
// =====================================================
function viewAllDonorsOnMap(requestId, hospitalLat, hospitalLng) {
  localStorage.setItem("selected_request_id", requestId);

  localStorage.setItem("hospital_latitude", hospitalLat);

  localStorage.setItem("hospital_longitude", hospitalLng);

  localStorage.removeItem("selected_donor_id");

  window.location.href = "donor-map.html";
}

// =====================================================
// VIEW SINGLE DONOR ON MAP
// =====================================================
function viewDonorOnMap(requestId, donorId) {
  localStorage.setItem("selected_request_id", requestId);

  localStorage.setItem("selected_donor_id", donorId);

  window.location.href = "donor-map.html";
}

// =====================================================
// RESPONSE STATUS CLASS
// =====================================================

function getResponseClass(response) {
  if (!response) {
    return "pending";
  }

  return response

    .toLowerCase()

    .replace(/\s+/g, "-");
}

// =====================================================
// REQUEST STATUS CLASS
// =====================================================

function getStatusClass(status) {
  if (!status) {
    return "";
  }

  return status

    .toLowerCase()

    .replace(/\s+/g, "-");
}

function formatUnits(value) {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return "N/A";
  }

  return `${numericValue} ${numericValue === 1 ? "unit" : "units"}`;
}

// =====================================================
// CANCEL REQUEST
// =====================================================

async function cancelRequest(requestId) {
  const confirmCancel = confirm(
    "Are you sure you want to cancel this blood request?",
  );

  if (!confirmCancel) {
    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/api/requests/${requestId}/cancel`,

      {
        method: "PATCH",

        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    const result = await response.json();

    if (!response.ok) {
      alert(result.message || "Failed to cancel request");

      return;
    }

    alert("Blood request cancelled successfully");

    loadMyRequests();
  } catch (error) {
    console.error(
      "Cancel Request Error:",

      error,
    );

    alert("Unable to connect to backend");
  }
}
// =====================================================
// COMPLETE DONATION
// =====================================================

async function completeDonation(requestId) {
  const confirmComplete = confirm(
    "Confirm that the blood donation has been completed?",
  );

  if (!confirmComplete) {
    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/api/requests/${requestId}/complete`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );

    const data = await response.json();

    if (!response.ok) {
      alert(data.message);
      return;
    }

    alert(data.message);

    loadMyRequests();
  } catch (error) {
    console.error(error);

    alert("Unable to connect to backend.");
  }
}

// =====================================================
// START
// =====================================================

loadMyRequests();

function goBackToDashboard() {
  const role = localStorage.getItem("role");

  if (role === "DONOR") {
    window.location.href = "donor-dashboard.html";
  } else if (role === "PATIENT") {
    window.location.href = "patient-dashboard.html";
  } else if (role === "ADMIN") {
    window.location.href = "admin-dashboard.html";
  } else {
    window.location.href = "login.html";
  }
}
