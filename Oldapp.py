import streamlit as st
import requests

st.set_page_config(page_title="CivicLens", layout="wide")

API_KEY = st.secrets["google"]["api_key"]

# IMPORTANT: this must be ABOVE the if-statements
menu = st.sidebar.radio(
    "Navigate",
    ["Home", "Polling Finder", "Deadlines", "Offices", "Candidates"]
)

# HOME
if menu == "Home":
    st.title("🗳️ CivicLens")
    st.write("Helping voters in NC-14")

# POLLING
elif menu == "Polling Finder":
    st.header("📍 Find Your Polling Place")

    address = st.text_input("Enter your full address")

    if st.button("Search"):
        if not address:
            st.error("Please enter an address.")
        else:
            url = ( "https://www.googleapis.com/civicinfo/v2/representatives" f"?address={address}" f"&key={API_KEY}" )
            response = requests.get(url)
            data = response.json()
            st.write(data)  # <-- TEMP DEBUG

            if "error" in data:
                st.error(data["error"]["message"])

            elif "pollingLocations" in data and data["pollingLocations"]:
                location = data["pollingLocations"][0]

                st.success("Polling location found!")

                address_data = location.get("address", {})

                st.subheader("📍 Your Polling Place")

                st.write(address_data.get("locationName", "Polling Location"))
                st.write(address_data.get("line1", ""))
                st.write(address_data.get("city", "") + ", " + address_data.get("state", ""))
                st.write(address_data.get("zip", ""))

            else:
                st.warning("Exact polling location not available.")

                if "state" in data:

                    state_info = data["state"][0]["electionAdministrationBody"]

                    st.subheader("🗳️ North Carolina Voting Resources")

                    st.markdown(
                    f"[Check Registration Status]({state_info.get('electionRegistrationConfirmationUrl', '#')})"
                    )

                    st.markdown(
                    f"[Register to Vote]({state_info.get('electionRegistrationUrl', '#')})"
                    )

                    st.markdown(
                        f"[Absentee Voting Info]({state_info.get('absenteeVotingInfoUrl', '#')})"
                    )

                    st.markdown(
                        f"[Voting Location Finder]({state_info.get('votingLocationFinderUrl', '#')})"
                    )

# DEADLINES
elif menu == "Deadlines":
    st.header("📅 Deadlines")

# OFFICES
elif menu == "Offices":
    st.header("🏛️ Offices")

# CANDIDATES
elif menu == "Candidates":
    st.header("🗳️ Candidates")