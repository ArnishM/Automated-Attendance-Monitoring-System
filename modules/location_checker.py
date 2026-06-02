"""
location_checker.py
===================
Validates that the user is inside the authorized classroom network
by checking their public IP address and city via an external API.

PL-2 Concepts: OOP, Requests API, Custom Exception Handling
"""

import requests
from modules.exceptions import LocationRestrictionError


class LocationChecker:
    """
    Checks whether the current machine is within the authorized
    classroom location by querying an IP geolocation service.

    Tries ipapi.co first. If that API is rate-limited (returns an
    error JSON with no city/country fields), it automatically falls
    back to ip-api.com so you always get a real result.
    """

    # (url, ip_key, city_key, region_key, country_key, org_key)
    API_URLS = [
        ("https://ipapi.co/json/",    "ip",    "city", "region",     "country_code", "org"),
        ("http://ip-api.com/json/",   "query", "city", "regionName", "countryCode",  "isp"),
    ]

    def __init__(self, allowed_city: str, allowed_country: str = None):
        """
        Args:
            allowed_city    : Name of the city where the classroom is located.
            allowed_country : (Optional) Country code, e.g. 'IN'. Adds extra validation.
        """
        self.allowed_city    = allowed_city.strip().lower()
        self.allowed_country = allowed_country.strip().upper() if allowed_country else None
        self._cached_location = None   # cache result to avoid repeated API calls

    def get_current_location(self) -> dict:
        """
        Fetches the current machine's public IP geo-information.
        Tries each API in API_URLS order, skipping any that return an error.

        Returns:
            dict with keys: ip, city, region, country_code, org
        Raises:
            ConnectionError if all APIs fail.
        """
        if self._cached_location:
            return self._cached_location

        last_error = "No API responded successfully."

        for (url, k_ip, k_city, k_region, k_country, k_org) in self.API_URLS:
            try:
                response = requests.get(url, timeout=6)
                response.raise_for_status()
                data = response.json()

                # Detect soft-error responses:
                #   ipapi.co rate-limit  -> {"error": true, "reason": "RateLimited", ...}
                #   ip-api.com failure   -> {"status": "fail", "message": "..."}
                if data.get("error") or data.get("status") == "fail":
                    reason = data.get("reason") or data.get("message") or "unknown reason"
                    print(f"   [Location] {url} returned error: {reason}. Trying fallback API...")
                    last_error = f"{url} error: {reason}"
                    continue

                self._cached_location = {
                    "ip"           : data.get(k_ip,      "N/A"),
                    "city"         : data.get(k_city,    "Unknown"),
                    "region"       : data.get(k_region,  "Unknown"),
                    "country_code" : data.get(k_country, "Unknown"),
                    "org"          : data.get(k_org,     "Unknown"),
                }
                return self._cached_location

            except requests.exceptions.ConnectionError:
                last_error = f"Could not reach {url}"
                continue
            except requests.exceptions.Timeout:
                last_error = f"{url} timed out after 6 seconds"
                continue
            except Exception as e:
                last_error = f"Unexpected error from {url}: {e}"
                continue

        raise ConnectionError(f"All geolocation APIs failed. Last error: {last_error}")

    def is_authorized(self) -> bool:
        """
        Checks if the current location matches the allowed classroom location.

        Returns:
            True if authorized.
        Raises:
            LocationRestrictionError if the location does not match.
        """
        info = self.get_current_location()
        current_city    = info["city"].strip().lower()
        current_country = info["country_code"].strip().upper()

        city_ok    = (current_city == self.allowed_city)
        country_ok = (self.allowed_country is None) or (current_country == self.allowed_country)

        if city_ok and country_ok:
            return True

        detected = f"{info['city']}, {info['country_code']}"
        allowed  = f"{self.allowed_city.title()}"
        if self.allowed_country:
            allowed += f", {self.allowed_country}"

        raise LocationRestrictionError(detected_location=detected, allowed_location=allowed)

    def print_location_info(self):
        """Utility: prints current IP location to console."""
        try:
            info = self.get_current_location()
            print("\n Current Location Info:")
            print(f"   IP Address : {info['ip']}")
            print(f"   City       : {info['city']}")
            print(f"   Region     : {info['region']}")
            print(f"   Country    : {info['country_code']}")
            print(f"   ISP/Org    : {info['org']}")
        except ConnectionError as e:
            print(f"[LocationChecker] Warning: {e}")
