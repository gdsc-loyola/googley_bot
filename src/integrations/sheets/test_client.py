import asyncio
from client import GoogleSheetsClient


async def main():
    spreadsheet_id = input("Enter Google Sheet ID: ").strip()
    client = GoogleSheetsClient()

    try:
        # Read values
        data = await client.get(spreadsheet_id, "Sheet1!A1:D5")
        print("\n[GET] Sheet data:")
        print(data)

        # Update values
        result = await client.post(spreadsheet_id, "Sheet1!A1", [["I love", "Caleb's BIG FAT COCK", "so much"]])
        print("\n[POST] Result:")
        print(result)

    except Exception as e:
        print(f"\n❌ Error: {e}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
