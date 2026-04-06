from langchain_core.tools import tool
from backend.services.hotel_service import get_hotels_by_location
from backend.utils.logger import logger


@tool
def search_hotels(location: str, sort_by_price: bool = False) -> str:
    """
    Search for hotels in a given location/city.
    Use this when the user asks to find hotels somewhere.
    Set sort_by_price=True when the user asks for cheap, budget, or affordable hotels.
    """

    logger.info(f"🔍 Searching hotels in: {location} | sort_by_price={sort_by_price}")

    try:
        hotels = get_hotels_by_location(location, sort_by_price=sort_by_price)

        if not hotels:
            return f"❌ No hotels found in {location}. Try another city."

        label = "cheapest first" if sort_by_price else f"{len(hotels)} found"
        result = f"🏨 Hotels in {location} ({label}):\n\n"

        for h in hotels:
            prices = sorted(r.price_per_night for r in h.room_types) if h.room_types else []
            price_line = f"From £{prices[0]:.0f}/night" if prices else "Price on request"

            result += (
                f"Hotel ID  : {h.id}\n"
                f"Name      : {h.name}\n"
                f"Location  : {h.location}\n"
                f"Price     : {price_line}\n"
                f"Rating    : {h.rating}⭐\n"
                f"Amenities : {h.amenities}\n"
                f"{'─' * 40}\n"
            )

        return result.strip()

    except Exception as e:
        logger.error(f"Error searching hotels: {e}")
        return f"❌ Error searching hotels: {str(e)}"