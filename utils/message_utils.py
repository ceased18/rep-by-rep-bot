import logging
import math

logger = logging.getLogger(__name__)

async def send_long_message(channel, content):
    """
    Send a message that might exceed Discord's 2000 character limit.
    Splits into multiple messages if needed, or truncates with a notice.
    """
    try:
        if len(content) <= 2000:
            await channel.send(content)
            return

        # Try to split by paragraphs first
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 1:
            current_message = ""
            for paragraph in paragraphs:
                if len(current_message) + len(paragraph) + 2 > 1900:  # Leave some margin
                    if current_message:
                        await channel.send(current_message)
                        logger.info(f"Sent split message part (length: {len(current_message)})")
                        current_message = paragraph + "\n\n"
                    else:
                        # Single paragraph too long, need to split by characters
                        chunks = math.ceil(len(paragraph) / 1900)
                        logger.info(f"Splitting long paragraph into {chunks} parts")
                        for i in range(chunks):
                            chunk = paragraph[i*1900:(i+1)*1900]
                            if i < chunks - 1:
                                chunk += " [continued...]"
                            await channel.send(chunk)
                            logger.info(f"Sent chunk {i+1}/{chunks} (length: {len(chunk)})")
                else:
                    current_message += paragraph + "\n\n"

            if current_message:
                await channel.send(current_message)
                logger.info(f"Sent final split message part (length: {len(current_message)})")
        else:
            # No paragraphs to split on, truncate
            truncated = content[:1500] + "... (truncated)"
            await channel.send(truncated)
            logger.warning(f"Message truncated from {len(content)} to 1500 characters")

    except Exception as e:
        logger.error(f"Error sending long message: {str(e)}")
        # Fallback to truncation
        await channel.send(content[:1500] + "... (truncated)")