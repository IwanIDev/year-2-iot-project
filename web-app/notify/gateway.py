"""Transport adapters for delivering notifications."""

from dataclasses import dataclass

import httpx


@dataclass(slots=True)
class MailgunGateway:
	"""Send email notifications through Mailgun."""

	mail_url: str
	mail_sender: str
	api_key: str
	api_base_url: str = "https://api.eu.mailgun.net/v3"

	def send_email(self, recipient: str, subject: str, text_content: str, html_content: str) -> httpx.Response:
		"""Send an email message and return the Mailgun response."""
		with httpx.Client() as client:
			return client.post(
				f"{self.api_base_url}/{self.mail_url}/messages",
				auth=httpx.BasicAuth(username="api", password=self.api_key),
				data={
					"from": self.mail_sender,
					"to": recipient,
					"subject": subject,
					"text": text_content,
					"html": html_content,
				},
				timeout=10,
			)
