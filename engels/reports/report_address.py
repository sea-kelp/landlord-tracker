#
# very basic address report
#
import sys

from sqlalchemy import select

from ..db import get_db_engine

def trunc(s, max=80):
    if len(s) > max:
        return s[:max-3] + "..."
    return s


def report(address):
    engine = get_db_engine()

    with engine.connect() as conn:
        
        apt_complex = conn.exec_driver_sql(f"""
        select * from stg_apartment_complex where address like '{address}%%'
        """).mappings().first()

        print(f"Address:       {apt_complex['address']}")
        print(f"Description:   {apt_complex['complex_descr']}")
        print(f"Parcel ID:     {apt_complex['major']} {apt_complex['minor']}")
        print()

        account_results  = conn.exec_driver_sql("""
        select * from stg_real_property_account where major = %s and minor = %s
        """, (apt_complex['major'], apt_complex['minor'])).mappings()

        accounts = list(account_results)

        # find distinct names and addresses
        taxpayer_names = set([account['taxpayer_name'] for account in accounts])
        addresses = set([account['address_normalized'] for account in accounts])

        print(("-" * 40) + "\n")

        print("Names found in taxpayer entries:\n")

        for taxpayer_name in taxpayer_names:
            print(f"{taxpayer_name}")

            other_apt_complexes = conn.exec_driver_sql("""
            select sac.*
            from stg_apartment_complex sac
            where major_minor in
                (select major_minor from stg_real_property_account where taxpayer_name = %s) 
            order by major_minor
            """, (taxpayer_name,)).mappings()

            print(f"  Apartment complexes with tax records with this name:")
            for other_apt_complex in other_apt_complexes:
                print(f"  {other_apt_complex['major_minor']} - {other_apt_complex['address_normalized']}")

            print("")

        print(("-" * 40) + "\n")

        print("Addresses found in taxpayer entries:\n")

        for address in addresses:
            print(f"{address}")
            
            other_apt_complexes = conn.exec_driver_sql("""
            select sac.*
            from stg_apartment_complex sac
            where major_minor in
                (select major_minor from stg_real_property_account where address_normalized = %s) 
            order by major_minor
            """, (address,)).mappings()

            print(f"  Apartment complexes with tax records with this address:")
            for other_apt_complex in other_apt_complexes:
                print(f"  {other_apt_complex['major_minor']} - {other_apt_complex['address_normalized']}")

            print("")

        complaints = conn.exec_driver_sql("""
        select * from stg_complaints where original_address1 = %s
        order by open_date desc
        """, (apt_complex['address'],)).mappings()

        print(("-" * 40) + "\n")

        print("Complaints:\n")

        for complaint in complaints:
            print(f"{complaint['open_date']} - {trunc(complaint['description'])}")


if __name__ == '__main__':
    report(sys.argv[1])
