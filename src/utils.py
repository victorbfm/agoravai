def remove_duplicates(channels):
    seen = set()
    unique_channels = []
    for channel in channels:
        if not channel.get("channel_id"):
            print(f"Aviso: Canal sem 'channel_id' foi ignorado: {channel}")
            continue
        if channel['channel_id'] not in seen:
            unique_channels.append(channel)
            seen.add(channel['channel_id'])
    return unique_channels
