let map = null;

let driverMarker = null;

let driverWatchId = null;

let customerTimer = null;


/* =====================================================
   CREATE MAP
===================================================== */

function startMap() {

    if (map !== null) {
        return;
    }

    map = L.map("map").setView(
        [15.3173, 75.7139],
        7
    );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,

            attribution:
                "© OpenStreetMap contributors"
        }
    ).addTo(map);
}


/* =====================================================
   DRIVER GPS
===================================================== */

function startDriverGPS() {

    startMap();

    const status =
        document.getElementById(
            "gps-status"
        );


    if (!navigator.geolocation) {

        status.innerText =
            "GPS is not supported by this browser.";

        return;
    }


    status.innerText =
        "Requesting your GPS location...";


    driverWatchId =
        navigator.geolocation.watchPosition(

            function(position) {

                const latitude =
                    position.coords.latitude;

                const longitude =
                    position.coords.longitude;

                const accuracy =
                    position.coords.accuracy;


                updateDriverMarker(
                    latitude,
                    longitude
                );


                sendDriverLocation(
                    latitude,
                    longitude
                );


                status.innerText =
                    "🟢 GPS is running";


                document.getElementById(
                    "gps-accuracy"
                ).innerText =
                    "Accuracy: "
                    + Math.round(accuracy)
                    + " meters";


                document.getElementById(
                    "coordinates"
                ).innerText =
                    "Coordinates: "
                    + latitude.toFixed(6)
                    + ", "
                    + longitude.toFixed(6);

            },


            function(error) {

                let message =
                    "GPS error.";


                if (error.code === 1) {

                    message =
                        "Location permission denied. Allow location access.";

                }


                if (error.code === 2) {

                    message =
                        "GPS location unavailable.";

                }


                if (error.code === 3) {

                    message =
                        "GPS request timed out.";

                }


                status.innerText =
                    "🔴 " + message;

            },


            {

                enableHighAccuracy: true,

                maximumAge: 0,

                timeout: 10000

            }

        );
}


/* =====================================================
   DRIVER MARKER
===================================================== */

function updateDriverMarker(
    latitude,
    longitude
) {

    if (driverMarker === null) {

        driverMarker =
            L.marker([
                latitude,
                longitude
            ]).addTo(map);


        driverMarker.bindPopup(
            "🚚 Your Lorry"
        );

    }

    else {

        driverMarker.setLatLng([
            latitude,
            longitude
        ]);

    }


    map.setView(
        [latitude, longitude],
        16
    );
}


/* =====================================================
   SEND DRIVER LOCATION
===================================================== */

function sendDriverLocation(
    latitude,
    longitude
) {

    fetch("/update-location", {

        method: "POST",

        headers: {
            "Content-Type":
                "application/json"
        },

        body: JSON.stringify({

            latitude: latitude,

            longitude: longitude

        })

    })

    .then(response =>
        response.json()
    )

    .then(data => {

        if (!data.success) {

            console.log(
                data.message
            );

        }

    })

    .catch(error => {

        console.log(
            "GPS server error:",
            error
        );

    });
}


/* =====================================================
   STOP DRIVER GPS
===================================================== */

function stopDriverGPS() {

    if (driverWatchId !== null) {

        navigator.geolocation.clearWatch(
            driverWatchId
        );

        driverWatchId = null;
    }


    const status =
        document.getElementById(
            "gps-status"
        );


    if (status) {

        status.innerText =
            "⛔ GPS stopped.";

    }
}


/* =====================================================
   CUSTOMER MAP
===================================================== */

function startCustomerMap(
    driverId = ""
) {

    startMap();

    getDriverLocation(
        driverId
    );


    customerTimer =
        setInterval(

            function() {

                getDriverLocation(
                    driverId
                );

            },

            3000

        );
}


/* =====================================================
   GET DRIVER LOCATION
===================================================== */

function getDriverLocation(
    driverId = ""
) {

    let url =
        "/driver-location";


    if (driverId) {

        url +=
            "?driver_id="
            + encodeURIComponent(
                driverId
            );

    }


    fetch(url)

        .then(response =>
            response.json()
        )

        .then(data => {

            const status =
                document.getElementById(
                    "customer-status"
                );


            if (!data.success) {

                status.innerText =
                    "🟡 Driver location is not available yet.";

                return;
            }


            const latitude =
                data.latitude;

            const longitude =
                data.longitude;


            if (driverMarker === null) {

                driverMarker =
                    L.marker([
                        latitude,
                        longitude
                    ]).addTo(map);


                driverMarker.bindPopup(
                    "🚚 Driver Location"
                );

            }

            else {

                driverMarker.setLatLng([
                    latitude,
                    longitude
                ]);

            }


            map.setView(
                [latitude, longitude],
                15
            );


            status.innerText =
                "🟢 Driver location received";


            document.getElementById(
                "driver-info"
            ).innerText =
                "Driver: "
                + data.driver_name;


            document.getElementById(
                "vehicle-info"
            ).innerText =
                "Vehicle: "
                + data.vehicle_number;


            document.getElementById(
                "driver-coordinates"
            ).innerText =
                "Location: "
                + latitude.toFixed(6)
                + ", "
                + longitude.toFixed(6);

        })


        .catch(error => {

            console.log(
                "Location request failed:",
                error
            );

        });
}