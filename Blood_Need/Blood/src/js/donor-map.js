const API_URL = "https://ai-blood-donor-matching-system.onrender.com";
const token = localStorage.getItem("token");
const requestId = localStorage.getItem("selected_request_id");
const selectedDonorId = localStorage.getItem("selected_donor_id");

const requestInfo = document.getElementById("requestInfo");

// =====================================================
// CHECK LOGIN
// =====================================================

if (!token || !requestId) {
  window.location.href = "login.html";
}

// =====================================================
// LOAD DONOR MAP
// =====================================================

async function loadMap() {
  try {
    const response = await fetch(`${API_URL}/api/matching/${requestId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const bloodRequest = await response.json();

    if (!response.ok) {
      throw new Error(bloodRequest.message || "Failed to load matching");
    }

    const matchedDonors = bloodRequest.matched_donors || [];

    // =================================================
    // REQUEST INFO
    // =================================================

    requestInfo.innerHTML = `

            <h2>Request #${bloodRequest.request_id}</h2>

            <p><strong>Blood Group:</strong>
            ${bloodRequest.blood_group}</p>

            <p><strong>Hospital:</strong>
            ${bloodRequest.hospital_name}</p>

            <p><strong>Emergency:</strong>
            ${bloodRequest.emergency_level}</p>

            <p><strong>Matched Donors:</strong>
            ${matchedDonors.length}</p>

        `;

    // =================================================
    // HOSPITAL LOCATION
    // =================================================

    const hospitalLat = parseFloat(bloodRequest.hospital_latitude);

    const hospitalLng = parseFloat(bloodRequest.hospital_longitude);

    // =================================================
    // VALID DONORS
    // =================================================

    const donors = matchedDonors.filter((match) => {
      return (
        match.donor &&
        match.donor.latitude != null &&
        match.donor.longitude != null &&
        match.donor.longitude !== undefined &&
        !isNaN(parseFloat(match.donor.latitude)) &&
        !isNaN(parseFloat(match.donor.longitude))
      );
    });

    // =================================================
    // MAP CENTER
    // =================================================

    let mapCenter;

    if (!isNaN(hospitalLat) && !isNaN(hospitalLng)) {
      mapCenter = [hospitalLat, hospitalLng];
    } else if (donors.length > 0) {
      mapCenter = [
        parseFloat(donors[0].donor.latitude),

        parseFloat(donors[0].donor.longitude),
      ];
    } else {
      mapCenter = [16.3067, 80.4365];
    }

    // =================================================
    // CREATE MAP
    // =================================================

    const map = L.map("donorMap").setView(mapCenter, 13);

    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",

      {
        attribution: "&copy; OpenStreetMap contributors",
      },
    ).addTo(map);

    const markerLocations = [];

    // =================================================
    // HOSPITAL MARKER
    // =================================================
    const hospitalIcon = L.icon({
      iconUrl:
        "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png",

      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",

      iconSize: [25, 41],

      iconAnchor: [12, 41],
    });

    L.marker([hospitalLat, hospitalLng], { icon: hospitalIcon }).addTo(map)
      .bindPopup(`
<b>🏥 Hospital</b>
<br>
${bloodRequest.hospital_name}
`);

    // =================================================
    // DONOR MARKERS
    // =================================================

    donors.forEach((match) => {
      const donor = match.donor;

      const donorLat = parseFloat(donor.latitude);

      const donorLng = parseFloat(donor.longitude);

      // ===============================
      // RED DONOR ICON
      // ===============================

      const icon = L.icon({
        iconUrl:
          "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",

        shadowUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",

        iconSize: [25, 41],

        iconAnchor: [12, 41],
      });

      const marker = L.marker([donorLat, donorLng], { icon }).addTo(map);

      marker.bindPopup(`

        <b>❤️ Matched Donor</b>

        <br><br>

        <b>Donor ID :</b>
        ${donor.donor_id}

        <br>

        <b>Blood Group :</b>
        ${donor.blood_group}

        <br>

        <b>Distance :</b>
        ${Number(match.distance_km).toFixed(2)} km

        <br>

        <b>Ranking Score :</b>
        ${Number(match.ranking_score ?? 0).toFixed(2)}

        <br>

        <b>Status :</b>
        ${match.donor_response}

    `);

      if (
        selectedDonorId &&
        String(selectedDonorId) === String(donor.donor_id)
      ) {
        marker.openPopup();
      }

      markerLocations.push([donorLat, donorLng]);

      if (!isNaN(hospitalLat) && !isNaN(hospitalLng)) {
        L.polyline(
          [
            [hospitalLat, hospitalLng],
            [donorLat, donorLng],
          ],

          {
            color: "#2563eb",
            weight: 5,
            opacity: 0.8,
            dashArray: "8,8",
          },
        ).addTo(map);
      }
    });

    // =================================================
    // FIT MAP
    // =================================================

    if (markerLocations.length > 1) {
      map.fitBounds(
        L.latLngBounds(markerLocations),

        {
          padding: [40, 40],
        },
      );
    }
  } catch (error) {
    console.error(error);

    requestInfo.innerHTML = `

            <p style="color:red">

                ${error.message}
 
            </p>

        `;
  }
}

// =====================================================
// START
// =====================================================

loadMap();
