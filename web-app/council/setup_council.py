from .Council import Council
from database import db

COUNCILS = [
        {"id": 1, "name": "Blaenau Gwent", "collectionName": "BlaenauGwentCountyBoroughCouncil", "url": "https://www.blaenau-gwent.gov.uk"},
        {"id": 2, "name": "Bridgend", "collectionName": None, "url": None},
        {"id": 3, "name": "Caerphilly", "collectionName": None, "url": None},
        {"id": 4, "name": "Cardiff", "collectionName": "CardiffCouncil", "url": "https://www.gov.uk"},
        {"id": 5, "name": "Carmarthenshire", "collectionName": "CarmarthenshireCountyCouncil", "url": "https://www.carmarthenshire.gov.wales"},
        {"id": 6, "name": "Ceredigion", "collectionName": "CeredigionCountyCouncil", "url": "https://www.ceredigion.gov.uk/resident/bins-recycling/"},
        {"id": 7, "name": "Conwy", "collectionName": "ConwyCountyBorough", "url": "https://www.conwy.gov.uk"},
        {"id": 8, "name": "Denbighshire", "collectionName": "DenbighshireCouncil", "url": "https://www.denbighshire.gov.uk/"},
        {"id": 9, "name": "Flintshire", "collectionName": "FlintshireCountyCouncil", "url": "https://digital.flintshire.gov.uk"},
        {"id": 10, "name": "Gwynedd", "collectionName": "GwyneddCouncil", "url": "https://diogel.gwynedd.llyw.cymru"},
        {"id": 11, "name": "Isle of Anglesey", "collectionName": "IsleOfAngleseyCouncil", "url": "https://www.anglesey.gov.wales/en/Residents/Bins-and-recycling/Waste-Collection-Day.aspx"},
        {"id": 12, "name": "Merthyr Tydfil", "collectionName": None, "url": None},
        {"id": 13, "name": "Monmouthshire", "collectionName": "MonmouthshireCountyCouncil", "url": "https://maps.monmouthshire.gov.uk"},
        {"id": 14, "name": "Neath Port Talbot", "collectionName": "NeathPortTalbotCouncil", "url": "https://www.npt.gov.uk"},
        {"id": 15, "name": "Newport", "collectionName": "NewportCityCouncil", "url": "https://www.newport.gov.uk/"},
        {"id": 16, "name": "Pembrokeshire", "collectionName": "PembrokeshireCountyCouncil", "url": "https://nearest.pembrokeshire.gov.uk/property"}, # TODO: The URL might need to have the UPRN added to it
        {"id": 17, "name": "Powys", "collectionName": "PowysCouncil", "url": "https://www.powys.gov.uk"},
        {"id": 18, "name": "Rhondda Cynon Taf", "collectionName": "RhonddaCynonTaffCouncil", "url": "https://www.rctcbc.gov.uk/EN/Resident/RecyclingandWaste/RecyclingandWasteCollectionDays.aspx"},
        {"id": 19, "name": "Swansea", "collectionName": "SwanseaCouncil", "url": "https://www1.swansea.gov.uk/recyclingsearch/"},
        {"id": 20, "name": "Torfaen", "collectionName": None, "url": None},
        {"id": 21, "name": "Vale of Glamorgan", "collectionName": "ValeofGlamorganCouncil", "url": "https://www.valeofglamorgan.gov.uk/en/living/Recycling-and-Waste/"},
        {"id": 22, "name": "Wrexham", "collectionName": "WrexhamCountyBoroughCouncil", "url": "https://www.wrexham.gov.uk/service/when-are-my-bins-collected"},
]

def setup_council():
    inserted = 0
    for council in COUNCILS:
        existing_council = Council.query.filter_by(name=council["name"]).first()
        if not existing_council:
            new_council = Council(
                id=council["id"],
                name=council["name"],
                collectionName=council["collectionName"] if council["collectionName"] else "",
                url=council["url"] if council["url"] else ""
            )
            db.session.add(new_council)
            inserted += 1

    if inserted:
        db.session.commit()

    return inserted

