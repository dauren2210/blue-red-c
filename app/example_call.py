import asyncio
import logging
from app.crud.crud_session import create_session, update_session, get_session
from app.crud.crud_supplier import create_supplier
from app.models.session import SessionCreate, SessionUpdate
from app.models.supplier import SupplierCreate
from app.api.endpoints.voice_call import initiate_call
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection

logging.basicConfig(level=logging.INFO)

async def main():
    await connect_to_mongo()
    try:
        # 1. Create session
        structured_request = {
            'product_name': 'Office chairs',
            'amount': '50',
            'date_and_time': '2025-07-09T11:00',
            'location': 'Paris, Le Carrousel du Louvre'
        }
        session_create = SessionCreate(suppliers=[])
        session = await create_session(session_create)
        logging.info(f"Created session: {session}")

        # 2. Create supplier
        supplier_create = SupplierCreate(
            name="Dauren GmbH",
            phone_numbers=["+491631830067"]
        )
        supplier = await create_supplier(supplier_create)
        logging.info(f"Created supplier: {supplier}")

        # 3. Update session to add supplier
        session.suppliers.append(supplier)
        session_update = SessionUpdate(suppliers=session.suppliers, structured_request=structured_request)
        updated_session = await update_session(str(session.id), session_update)
        logging.info(f"Updated session with supplier: {updated_session}")

        # 4. Place call to each supplier (first phone number only)
        for supp in updated_session.suppliers:
            if supp.phone_numbers:
                phone = supp.phone_numbers[0]
                logging.info(f"Placing call to supplier {supp.name} at {phone}")
                try:
                    # Use Twilio phone number from config
                    from_phone = settings.TWILIO_PHONE_NUMBER
                    # This will use the /twiml endpoint as per voice_call.py
                    result = await initiate_call(supplier_phone=phone, from_phone=from_phone)
                    logging.info(f"Call result: {result}")
                except Exception as e:
                    
                    logging.error(f"Failed to place call to {phone}: {e}")
            else:
                logging.warning(f"Supplier {supp.name} has no phone numbers.")
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main()) 