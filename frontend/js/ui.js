const messages = document.getElementById("messages");
const status = document.getElementById("status");
const typing = document.getElementById("typing");

// ============================================================
// STATUS
// ============================================================

export function setStatus(text) {

    if (status) {
        status.textContent = text;
    }

}


// ============================================================
// TYPING
// ============================================================

export function showTyping() {

    if (typing) {
        typing.classList.remove("hidden");
    }

}


export function hideTyping() {

    if (typing) {
        typing.classList.add("hidden");
    }

}


// ============================================================
// USER MESSAGE
// ============================================================

export function addUserMessage(text) {

    if (!messages) {
        return;
    }

    const message =
        document.createElement("div");

    message.className =
        "user-message";

    const label =
        document.createElement("strong");

    label.textContent =
        "👤 You";

    const content =
        document.createElement("div");

    content.textContent =
        text;

    message.appendChild(label);
    message.appendChild(content);

    messages.appendChild(
        message
    );

    scrollToBottom();

}


// ============================================================
// EMMA MESSAGE
// ============================================================

export function addEmmaMessage(text) {

    if (!messages) {
        return;
    }

    const message =
        document.createElement("div");

    message.className =
        "emma-message";

    const label =
        document.createElement("strong");

    label.textContent =
        "🤖 Emma";

    const content =
        document.createElement("div");

    content.textContent =
        text;

    message.appendChild(label);
    message.appendChild(content);

    messages.appendChild(
        message
    );

    scrollToBottom();

}


// ============================================================
// BOOKING CONFIRMATION
// ============================================================

export function addBookingConfirmation(
    appointment
) {

    if (!messages) {
        return;
    }

    // Remove previous booking card if one exists.
    const existing =
        document.getElementById(
            "emma-booking-confirmation"
        );

    if (existing) {
        existing.remove();
    }


    const card =
        document.createElement("div");

    card.id =
        "emma-booking-confirmation";

    card.className =
        "booking-confirmation";


    // ----------------------------------------
    // Header
    // ----------------------------------------

    const header =
        document.createElement("div");

    header.className =
        "booking-confirmation-header";

    header.textContent =
        "✓ Appointment Confirmed";


    // ----------------------------------------
    // Demo label
    // ----------------------------------------

    const demoLabel =
        document.createElement("div");

    demoLabel.className =
        "booking-demo-label";

    demoLabel.textContent =
        "EMMA DEMO";


    // ----------------------------------------
    // Details
    // ----------------------------------------

    const details =
        document.createElement("div");

    details.className =
        "booking-details";


    addBookingRow(
        details,
        "Patient",
        appointment.customer_name
    );

    addBookingRow(
        details,
        "Service",
        appointment.service
    );

    addBookingRow(
        details,
        "Date",
        appointment.appointment_date
    );

    addBookingRow(
        details,
        "Time",
        appointment.appointment_time
    );

    addBookingRow(
        details,
        "Email",
        appointment.email
    );

    addBookingRow(
        details,
        "Confirmation",
        appointment.confirmation_id
    );


    // ----------------------------------------
    // Demo notice
    // ----------------------------------------

    const notice =
        document.createElement("div");

    notice.className =
        "booking-demo-notice";

    notice.innerHTML = `
        <strong>DEMO MODE</strong>
        <br>
        The appointment confirmation has been
        prepared, but no real email has been sent.
    `;


    // ----------------------------------------
    // CruziLux CTA
    // ----------------------------------------

    const cta =
        document.createElement("div");

    cta.className =
        "booking-cta";


    const ctaTitle =
        document.createElement("div");

    ctaTitle.className =
        "booking-cta-title";

    ctaTitle.textContent =
        "Want Emma for your business?";


    const ctaText =
        document.createElement("div");

    ctaText.className =
        "booking-cta-text";

    ctaText.textContent =
        "See Emma running with real email, calendar and business integrations.";


    const contactButton =
        document.createElement("button");

    contactButton.className =
        "booking-contact-button";

    contactButton.textContent =
        "Contact CruziLux →";


    contactButton.addEventListener(
        "click",
        () => {

            window.dispatchEvent(
                new CustomEvent(
                    "cruzilux-contact-requested"
                )
            );

            console.log(
                "📩 CruziLux contact requested"
            );

        }
    );


    cta.appendChild(
        ctaTitle
    );

    cta.appendChild(
        ctaText
    );

    cta.appendChild(
        contactButton
    );


    // ----------------------------------------
    // Build card
    // ----------------------------------------

    card.appendChild(
        demoLabel
    );

    card.appendChild(
        header
    );

    card.appendChild(
        details
    );

    card.appendChild(
        notice
    );

    card.appendChild(
        cta
    );


    messages.appendChild(
        card
    );

    scrollToBottom();

}


// ============================================================
// BOOKING ROW
// ============================================================

function addBookingRow(
    parent,
    label,
    value
) {

    const row =
        document.createElement("div");

    row.className =
        "booking-row";


    const labelElement =
        document.createElement("span");

    labelElement.className =
        "booking-label";

    labelElement.textContent =
        `${label}:`;


    const valueElement =
        document.createElement("span");

    valueElement.className =
        "booking-value";

    valueElement.textContent =
        value || "-";


    row.appendChild(
        labelElement
    );

    row.appendChild(
        valueElement
    );


    parent.appendChild(
        row
    );

}


// ============================================================
// SCROLL
// ============================================================

function scrollToBottom() {

    if (!messages) {
        return;
    }

    messages.scrollTop =
        messages.scrollHeight;

}