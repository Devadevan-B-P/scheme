/**
 * Utility functions for filtering and calculating distance to nearby authorized channel partners.
 */

// Approximate coordinates for common districts for distance calculation (fallback)
const DISTRICT_COORDS = {
  'thiruvananthapuram': { lat: 8.5241, lng: 76.9366 },
  'ernakulam': { lat: 9.9816, lng: 76.2999 },
  'kozhikode': { lat: 11.2588, lng: 75.7804 },
  'kollam': { lat: 8.8932, lng: 76.6141 },
  'thrissur': { lat: 10.5276, lng: 76.2144 },
  'bengaluru': { lat: 12.9716, lng: 77.5946 },
  'chennai': { lat: 13.0827, lng: 80.2707 },
  'delhi': { lat: 28.6139, lng: 77.2090 },
  'mumbai': { lat: 19.0760, lng: 72.8777 },
}

/**
 * Calculate distance in kilometers between two lat/lng coordinates (Haversine formula).
 */
export function calculateHaversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371 // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

/**
 * Filter and sort partners by proximity to user and scheme compatibility.
 * 
 * @param {Array} partners - List of all partners.
 * @param {Object} scheme - The recommended scheme object.
 * @param {Object} userProfile - The beneficiary's profile containing district, pinCode, state.
 * @returns {Array} List of matching partners with computed distance strings and numeric distance.
 */
export function getNearbyPartnersForScheme(partners = [], scheme = null, userProfile = {}) {
  if (!partners || partners.length === 0) return []

  const schemeName = scheme?.name?.toLowerCase() || ''
  const schemeId = scheme?.id?.toLowerCase() || scheme?.scheme_id?.toLowerCase() || ''
  const userDistrict = (userProfile?.district || 'Thiruvananthapuram').trim().toLowerCase()

  return partners
    .filter((partner) => {
      if (!scheme) return true
      // Match by scheme name or ID or if partner supports all schemes
      const supported = partner.supportedSchemes || partner.schemes_served || []
      if (supported.length === 0) return true
      return supported.some((s) => {
        const sLower = s.toLowerCase()
        return (
          sLower.includes(schemeName) ||
          schemeName.includes(sLower) ||
          (schemeId && sLower.includes(schemeId)) ||
          sLower === "all"
        )
      })
    })
    .map((partner) => {
      // Calculate or format distance relative to user
      let distanceKm = partner.distance_km || 3.5
      let distanceText = partner.distance || partner.distance_formatted || `${distanceKm} km away`

      const pLat = partner.lat ?? partner.latitude
      const pLng = partner.lng ?? partner.longitude

      if (pLat && pLng && DISTRICT_COORDS[userDistrict]) {
        const userCoord = DISTRICT_COORDS[userDistrict]
        const km = calculateHaversineDistance(userCoord.lat, userCoord.lng, pLat, pLng)
        distanceKm = Math.round(km * 10) / 10
        distanceText = `${distanceKm} km away`
      } else if (partner.district && partner.district.toLowerCase() === userDistrict) {
        // In the same district
        distanceKm = parseFloat(partner.distance) || 2.4
        distanceText = `${distanceKm} km away`
      } else if (partner.distance) {
        distanceKm = parseFloat(partner.distance) || 4.5
        distanceText = partner.distance
      }

      return {
        ...partner,
        distanceKm,
        calculatedDistanceText: distanceText,
        matchesUserDistrict: partner.district ? partner.district.toLowerCase() === userDistrict : true,
      }
    })
    .sort((a, b) => {
      // Prioritize same district, then closer distance
      if (a.matchesUserDistrict && !b.matchesUserDistrict) return -1
      if (!a.matchesUserDistrict && b.matchesUserDistrict) return 1
      return a.distanceKm - b.distanceKm
    })
}
