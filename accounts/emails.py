from djoser import email


class CustomActivationEmail(email.ActivationEmail):
    html_template_name = "templates/emails/activation.html" 

    def get_context_data(self):
        context = super().get_context_data()
        user = context.get("user")

        context["username"] = user.full_name() or user.email.split("@")[0]
        context["site_name"] = "Bus Ticket Booking"
        context["support_email"] = "support@busticket.com"
        context["company_address"] = "123 Main St, Dar es Salaam, Tanzania"

        return context
