import logging
import math

logger = logging.getLogger(__name__)

async def send_long_message(channel, content):
    """
    Send a message that might exceed Discord's 2000 character limit.
    Splits into multiple messages if needed, preserving minimal formatting.
    """
    try:
        if len(content) <= 2000:
            await channel.send(content)
            return

        # Split by double newlines to preserve paragraph structure
        paragraphs = content.split('\n\n')
        current_message = ""

        for paragraph in paragraphs:
            # Clean up paragraph formatting
            formatted_paragraph = paragraph.strip()

            # Check if adding this paragraph would exceed limit
            if len(current_message) + len(formatted_paragraph) + 2 > 1900:
                if current_message:
                    await channel.send(current_message)
                    logger.info(f"Sent message part (length: {len(current_message)})")
                    current_message = formatted_paragraph
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
                if current_message:
                    is_bullet = formatted_paragraph.strip().startswith(('- ', '• '))
                    prev_was_bullet = current_message.strip().endswith(('- ', '• ')) or \
                                    any(line.strip().startswith(('- ', '• ')) for line in current_message.split('\n')[-2:])
                    if formatted_paragraph.startswith('**') and formatted_paragraph.endswith('**'):
                        # Add a blank line before headers
                        current_message += '\n\n'
                    elif is_bullet and prev_was_bullet:
                        # Only a single line break between consecutive bullets
                        current_message += '\n'
                    else:
                        # Normal paragraph spacing
                        current_message += '\n\n'
                current_message += formatted_paragraph

        if current_message:
            await channel.send(current_message)
            logger.info(f"Sent final message part (length: {len(current_message)})")

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        # Fallback: try to send without formatting
        await channel.send(content[:1900] + "\n[Message truncated due to length]")