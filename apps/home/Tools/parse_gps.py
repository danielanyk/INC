import re

def extract_timestamped_nmea(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    text = data.decode('ascii', errors='ignore')

    print("=== Start of decoded text ===")
    print(text[:1000])
    print("=== End of preview ===")

    # Split by timestamp blocks
    blocks = re.split(r"\[(\d+)\]\s*", text)
    
    results = []
    for i in range(1, len(blocks), 2):  # odd indexes are timestamps
        timestamp = blocks[i]
        content = blocks[i + 1]

        # Extract all NMEA lines (start with $GPxxx)
        lines = re.findall(r"\$GP[^\r\n]+", content)
        for line in lines:
            results.append((timestamp, line))

    print(f"Found {len(results)} GPS entries")
    for ts, sentence in results[:10]:  # print first 10
        print(f"Timestamp: {ts}, NMEA: {sentence}")

    return results

if __name__ == "__main__":
    extract_timestamped_nmea(r"C:\temp\gpslog.bin")