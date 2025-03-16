import logging
import math

logger = logging.getLogger(__name__)

async def send_long_message(channel, content):
    """
    Send a message that might exceed Discord's 2000 character limit.
    Splits into multiple messages if needed, preserving formatting.
    """
    try:
        if len(content) <= 2000:
            await channel.send(content)
            return

        # Split by double newlines to preserve paragraph structure
        paragraphs = content.split('\n\n')
        current_message = ""

        for paragraph in paragraphs:
            # Preserve single line breaks within paragraphs
            formatted_paragraph = paragraph.strip()

            # Add spacing after headers
            if formatted_paragraph.startswith('**') and formatted_paragraph.endswith('**'):
                formatted_paragraph += '\n'

            # Check if adding this paragraph would exceed limit
            if len(current_message) + len(formatted_paragraph) + 2 > 1900:
                if current_message:
                    await channel.send(current_message)
                    logger.info(f"Sent message part (length: {len(current_message)})")
                    current_message = formatted_paragraph + "\n\n"
                else:
                    # Single paragraph too long, need to split carefully
                    chunks = math.ceil(len(formatted_paragraph) / 1900)
                    logger.info(f"Splitting long paragraph into {chunks} parts")

                    for i in range(chunks):
                        chunk = formatted_paragraph[i*1900:(i+1)*1900]
                        if i < chunks - 1 and not chunk.endswith('\n'):
                            chunk += " [continued...]"
                        await channel.send(chunk)
                        logger.info(f"Sent chunk {i+1}/{chunks}")
            else:
                if current_message and not current_message.endswith('\n\n'):
                    current_message += '\n\n'
                current_message += formatted_paragraph

        if current_message:
            await channel.send(current_message)
            logger.info(f"Sent final message part (length: {len(current_message)})")

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        # Fallback: try to send without formatting
        await channel.send(content[:1900] + "\n[Message truncated due to length]")