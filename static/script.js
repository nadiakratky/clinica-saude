// ========================================
// ELEMENTOS DO AGENDAMENTO
// ========================================

const specialtyInput =
    document.getElementById(
        "appointment-specialty"
    );

const dateInput =
    document.getElementById(
        "appointment-date"
    );

const searchTimesButton =
    document.getElementById(
        "search-times"
    );

const dateMessage =
    document.getElementById(
        "date-message"
    );

const timesSection =
    document.getElementById(
        "times-section"
    );

const availableTimesContainer =
    document.getElementById(
        "available-times"
    );

const appointmentForm =
    document.getElementById(
        "appointment-form"
    );

const patientNameInput =
    document.getElementById(
        "patient-name"
    );

const patientPhoneInput =
    document.getElementById(
        "patient-phone"
    );

const selectedTimeElement =
    document.getElementById(
        "selected-time"
    );


// ========================================
// MODAL
// ========================================

const confirmationModal =
    document.getElementById(
        "confirmation-modal"
    );

const modalAppointmentDetails =
    document.getElementById(
        "modal-appointment-details"
    );

const closeConfirmationModal =
    document.getElementById(
        "close-confirmation-modal"
    );


// ========================================
// FUNCIONÁRIO
// ========================================

const employeeMenuButton =
    document.getElementById(
        "employee-menu-button"
    );

const employeeArea =
    document.getElementById(
        "employee-area"
    );

const employeeLoginCard =
    document.getElementById(
        "employee-login-card"
    );

const employeeLoginForm =
    document.getElementById(
        "employee-login-form"
    );

const employeePassword =
    document.getElementById(
        "employee-password"
    );

const employeeLoginMessage =
    document.getElementById(
        "employee-login-message"
    );

const employeePanel =
    document.getElementById(
        "employee-panel"
    );

const employeeLogoutButton =
    document.getElementById(
        "employee-logout-button"
    );

const appointmentsList =
    document.getElementById(
        "appointments-list"
    );

const appointmentsCounter =
    document.getElementById(
        "appointments-counter"
    );


// ========================================
// VARIÁVEIS
// ========================================

let selectedSpecialty = null;
let selectedDate = null;
let selectedTime = null;


// ========================================
// DATA ATUAL
// ========================================

function getTodayDate() {

    const today =
        new Date();

    const year =
        today.getFullYear();

    const month =
        String(
            today.getMonth() + 1
        ).padStart(
            2,
            "0"
        );

    const day =
        String(
            today.getDate()
        ).padStart(
            2,
            "0"
        );


    return (
        `${year}-${month}-${day}`
    );

}


const todayDate =
    getTodayDate();


dateInput.value =
    todayDate;

dateInput.min =
    todayDate;

dateInput.max =
    "2026-12-31";


// ========================================
// MUDOU ESPECIALIDADE
// ========================================

specialtyInput.addEventListener(
    "change",
    function () {

        selectedSpecialty =
            null;

        selectedTime =
            null;

        timesSection.classList.add(
            "hidden"
        );

        appointmentForm.classList.add(
            "hidden"
        );

        availableTimesContainer.innerHTML =
            "";

        clearMessage(
            dateMessage
        );

    }
);


// ========================================
// BUSCAR HORÁRIOS
// ========================================

searchTimesButton.addEventListener(
    "click",
    async function () {

        const specialty =
            specialtyInput.value;

        const date =
            dateInput.value;


        clearMessage(
            dateMessage
        );


        timesSection.classList.add(
            "hidden"
        );

        appointmentForm.classList.add(
            "hidden"
        );

        availableTimesContainer.innerHTML =
            "";


        selectedSpecialty =
            null;

        selectedDate =
            null;

        selectedTime =
            null;


        if (!specialty) {

            showMessage(
                dateMessage,
                "Selecione uma especialidade.",
                "error"
            );

            return;
        }


        if (!date) {

            showMessage(
                dateMessage,
                "Escolha uma data para consultar os horários.",
                "error"
            );

            return;
        }


        try {

            searchTimesButton.disabled =
                true;

            searchTimesButton.textContent =
                "Buscando...";


            const response =
                await fetch(

                    `/available?date=${encodeURIComponent(date)}&specialty=${encodeURIComponent(specialty)}`

                );


            const data =
                await response.json();


            if (!response.ok) {

                showMessage(
                    dateMessage,
                    data.error ||
                    data.message ||
                    "Não foi possível consultar os horários.",
                    "error"
                );

                return;
            }


            if (
                !data.available ||
                data.available.length === 0
            ) {

                showMessage(
                    dateMessage,
                    data.message ||
                    "Não há horários disponíveis para esta data.",
                    "error"
                );

                return;
            }


            selectedSpecialty =
                specialty;

            selectedDate =
                date;


            showMessage(
                dateMessage,
                `Horários disponíveis para ${specialty}.`,
                "success"
            );


            renderAvailableTimes(
                data.available
            );


        } catch (error) {

            console.error(
                error
            );


            showMessage(
                dateMessage,
                "Não foi possível conectar ao servidor.",
                "error"
            );


        } finally {

            searchTimesButton.disabled =
                false;

            searchTimesButton.textContent =
                "Buscar horários";

        }

    }
);


// ========================================
// MOSTRAR HORÁRIOS
// ========================================

function renderAvailableTimes(
    times
) {

    availableTimesContainer.innerHTML =
        "";


    times.forEach(
        function (time) {

            const button =
                document.createElement(
                    "button"
                );


            button.type =
                "button";

            button.classList.add(
                "time-button"
            );

            button.textContent =
                time;


            button.addEventListener(
                "click",
                function () {

                    selectTime(
                        time,
                        button
                    );

                }
            );


            availableTimesContainer.appendChild(
                button
            );

        }
    );


    timesSection.classList.remove(
        "hidden"
    );

}


// ========================================
// SELECIONAR HORÁRIO
// ========================================

function selectTime(
    time,
    clickedButton
) {

    selectedTime =
        time;


    const buttons =
        availableTimesContainer.querySelectorAll(
            ".time-button"
        );


    buttons.forEach(
        function (button) {

            button.classList.remove(
                "selected"
            );

        }
    );


    clickedButton.classList.add(
        "selected"
    );


    selectedTimeElement.textContent =
        `${selectedSpecialty} • ${time}`;


    appointmentForm.classList.remove(
        "hidden"
    );

}


// ========================================
// CRIAR AGENDAMENTO
// ========================================

appointmentForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        const patientName =
            patientNameInput.value.trim();

        const phone =
            patientPhoneInput.value.trim();


        if (
            !selectedSpecialty ||
            !selectedDate ||
            !selectedTime
        ) {

            showMessage(
                dateMessage,
                "Escolha especialidade, data e horário.",
                "error"
            );

            return;
        }


        if (
            !patientName ||
            !phone
        ) {

            showMessage(
                dateMessage,
                "Preencha seu nome e telefone.",
                "error"
            );

            return;
        }


        const appointmentData = {

            patient_name:
                patientName,

            phone:
                phone,

            specialty:
                selectedSpecialty,

            date:
                selectedDate,

            time:
                selectedTime

        };


        const submitButton =
            appointmentForm.querySelector(
                ".confirm-button"
            );


        try {

            submitButton.disabled =
                true;

            submitButton.textContent =
                "Confirmando...";


            const response =
                await fetch(
                    "/appointments",
                    {

                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                appointmentData
                            )

                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                showMessage(
                    dateMessage,
                    data.error ||
                    "Não foi possível criar o agendamento.",
                    "error"
                );

                return;
            }


            modalAppointmentDetails.textContent =

                `${patientName} • ${selectedSpecialty} • ${formatDate(selectedDate)} às ${selectedTime} • Horário de Brasília`;


            confirmationModal.classList.remove(
                "hidden"
            );


            patientNameInput.value =
                "";

            patientPhoneInput.value =
                "";


            appointmentForm.classList.add(
                "hidden"
            );


            await updateAvailableTimes();


            if (
                !employeePanel.classList.contains(
                    "hidden"
                )
            ) {

                await loadAppointments();

            }


        } catch (error) {

            console.error(
                error
            );


            showMessage(
                dateMessage,
                "Erro de comunicação com o servidor.",
                "error"
            );


        } finally {

            submitButton.disabled =
                false;

            submitButton.textContent =
                "Confirmar agendamento";

        }

    }
);


// ========================================
// ATUALIZAR HORÁRIOS
// ========================================

async function updateAvailableTimes() {

    if (
        !selectedDate ||
        !selectedSpecialty
    ) {

        return;

    }


    try {

        const response =
            await fetch(

                `/available?date=${encodeURIComponent(selectedDate)}&specialty=${encodeURIComponent(selectedSpecialty)}`

            );


        const data =
            await response.json();


        if (!response.ok) {

            return;

        }


        if (
            !data.available ||
            data.available.length === 0
        ) {

            availableTimesContainer.innerHTML =
                "";

            timesSection.classList.add(
                "hidden"
            );

            return;
        }


        renderAvailableTimes(
            data.available
        );


        selectedTime =
            null;

        selectedTimeElement.textContent =
            "-";


    } catch (error) {

        console.error(
            "Erro ao atualizar horários:",
            error
        );

    }

}


// ========================================
// MODAL
// ========================================

closeConfirmationModal.addEventListener(
    "click",
    function () {

        confirmationModal.classList.add(
            "hidden"
        );

    }
);


confirmationModal.addEventListener(
    "click",
    function (event) {

        if (
            event.target ===
            confirmationModal
        ) {

            confirmationModal.classList.add(
                "hidden"
            );

        }

    }
);


// ========================================
// FUNCIONÁRIO
// ========================================

employeeMenuButton.addEventListener(
    "click",
    async function () {

        employeeArea.classList.remove(
            "hidden"
        );


        employeeArea.scrollIntoView({

            behavior:
                "smooth",

            block:
                "start"

        });


        await checkEmployeeStatus();

    }
);


async function checkEmployeeStatus() {

    try {

        const response =
            await fetch(
                "/employee/status"
            );


        const data =
            await response.json();


        if (data.authenticated) {

            showEmployeePanel();

            await loadAppointments();

        } else {

            showEmployeeLogin();

        }


    } catch (error) {

        console.error(
            error
        );

        showEmployeeLogin();

    }

}


// ========================================
// LOGIN
// ========================================

employeeLoginForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        clearMessage(
            employeeLoginMessage
        );


        const password =
            employeePassword.value;


        if (!password) {

            showMessage(
                employeeLoginMessage,
                "Digite a senha.",
                "error"
            );

            return;
        }


        const button =
            employeeLoginForm.querySelector(
                ".employee-login-button"
            );


        try {

            button.disabled =
                true;

            button.textContent =
                "Entrando...";


            const response =
                await fetch(
                    "/employee/login",
                    {

                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify({

                                password:
                                    password

                            })

                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                showMessage(
                    employeeLoginMessage,
                    data.error ||
                    "Não foi possível realizar o login.",
                    "error"
                );

                return;
            }


            employeePassword.value =
                "";


            showEmployeePanel();

            await loadAppointments();


        } catch (error) {

            console.error(
                error
            );


            showMessage(
                employeeLoginMessage,
                "Erro de comunicação com o servidor.",
                "error"
            );


        } finally {

            button.disabled =
                false;

            button.textContent =
                "Acessar painel";

        }

    }
);


// ========================================
// LOGOUT
// ========================================

employeeLogoutButton.addEventListener(
    "click",
    async function () {

        try {

            await fetch(
                "/employee/logout",
                {
                    method:
                        "POST"
                }
            );


            appointmentsList.innerHTML =
                "";


            showEmployeeLogin();


        } catch (error) {

            console.error(
                error
            );

        }

    }
);


function showEmployeeLogin() {

    employeePanel.classList.add(
        "hidden"
    );

    employeeLoginCard.classList.remove(
        "hidden"
    );

}


function showEmployeePanel() {

    employeeLoginCard.classList.add(
        "hidden"
    );

    employeePanel.classList.remove(
        "hidden"
    );

}


// ========================================
// CARREGAR AGENDAMENTOS
// ========================================

async function loadAppointments() {

    try {

        const response =
            await fetch(
                "/appointments"
            );


        const data =
            await response.json();


        if (
            response.status === 401
        ) {

            showEmployeeLogin();

            return;
        }


        if (!response.ok) {

            throw new Error(
                "Erro ao carregar agendamentos."
            );

        }


        renderAppointments(
            data
        );


    } catch (error) {

        console.error(
            error
        );


        appointmentsList.innerHTML = `

            <div class="empty-state">

                <p>
                    Não foi possível carregar os agendamentos.
                </p>

            </div>

        `;

    }

}


// ========================================
// MOSTRAR CONSULTAS
// ========================================

function renderAppointments(
    appointments
) {

    appointmentsList.innerHTML =
        "";


    if (
        !appointments ||
        appointments.length === 0
    ) {

        appointmentsCounter.textContent =
            "Nenhuma consulta cadastrada.";


        appointmentsList.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    ♡
                </div>

                <p>
                    Nenhum agendamento encontrado.
                </p>

            </div>

        `;


        return;
    }


    const total =
        appointments.length;


    appointmentsCounter.textContent =
        total === 1
            ? "1 consulta agendada."
            : `${total} consultas agendadas.`;



    appointments.forEach(
        function (appointment) {

            const card =
                document.createElement(
                    "article"
                );


            card.classList.add(
                "appointment-item"
            );


            const title =
                document.createElement(
                    "h3"
                );


            title.textContent =
                appointment.patient_name;


            const specialtyBadge =
                document.createElement(
                    "span"
                );


            specialtyBadge.classList.add(
                "appointment-specialty"
            );


            specialtyBadge.textContent =
                appointment.specialty;


            const details =
                document.createElement(
                    "div"
                );


            details.classList.add(
                "appointment-details"
            );


            details.appendChild(
                createDetail(
                    "Data",
                    formatDate(
                        appointment.date
                    )
                )
            );


            details.appendChild(
                createDetail(
                    "Horário",
                    appointment.time
                )
            );


            details.appendChild(
                createDetail(
                    "Telefone",
                    appointment.phone
                )
            );


            const actions =
                document.createElement(
                    "div"
                );


            actions.classList.add(
                "appointment-actions"
            );


            const editButton =
                document.createElement(
                    "button"
                );


            editButton.type =
                "button";

            editButton.classList.add(
                "edit-appointment-button"
            );

            editButton.textContent =
                "Reagendar";


            editButton.addEventListener(
                "click",
                function () {

                    openReschedulePanel(
                        appointment,
                        card
                    );

                }
            );


            const deleteButton =
                document.createElement(
                    "button"
                );


            deleteButton.type =
                "button";

            deleteButton.classList.add(
                "delete-appointment-button"
            );

            deleteButton.textContent =
                "Cancelar";


            deleteButton.addEventListener(
                "click",
                function () {

                    cancelAppointment(
                        appointment
                    );

                }
            );


            actions.appendChild(
                editButton
            );

            actions.appendChild(
                deleteButton
            );


            card.appendChild(
                specialtyBadge
            );

            card.appendChild(
                title
            );

            card.appendChild(
                details
            );

            card.appendChild(
                actions
            );


            appointmentsList.appendChild(
                card
            );

        }
    );

}


// ========================================
// REAGENDAR
// ========================================

function openReschedulePanel(
    appointment,
    card
) {

    document
        .querySelectorAll(
            ".reschedule-panel"
        )
        .forEach(
            function (panel) {

                panel.remove();

            }
        );


    const panel =
        document.createElement(
            "div"
        );


    panel.classList.add(
        "reschedule-panel"
    );


    const heading =
        document.createElement(
            "div"
        );


    heading.classList.add(
        "reschedule-heading"
    );


    const headingTitle =
        document.createElement(
            "strong"
        );


    headingTitle.textContent =
        "Reagendar consulta";


    const headingText =
        document.createElement(
            "span"
        );


    headingText.textContent =
        `${appointment.specialty} • escolha a nova data e horário.`;


    heading.appendChild(
        headingTitle
    );

    heading.appendChild(
        headingText
    );


    const dateGroup =
        document.createElement(
            "div"
        );


    dateGroup.classList.add(
        "reschedule-form-group"
    );


    const dateLabel =
        document.createElement(
            "label"
        );


    dateLabel.textContent =
        "Nova data";


    const newDateInput =
        document.createElement(
            "input"
        );


    newDateInput.type =
        "date";

    newDateInput.min =
        todayDate;

    newDateInput.max =
        "2026-12-31";


    newDateInput.value =
        appointment.date >= todayDate
            ? appointment.date
            : todayDate;


    dateGroup.appendChild(
        dateLabel
    );

    dateGroup.appendChild(
        newDateInput
    );


    const searchButton =
        document.createElement(
            "button"
        );


    searchButton.type =
        "button";

    searchButton.classList.add(
        "reschedule-search-button"
    );

    searchButton.textContent =
        "Ver horários";


    const message =
        document.createElement(
            "div"
        );


    message.classList.add(
        "reschedule-message"
    );


    const timesContainer =
        document.createElement(
            "div"
        );


    timesContainer.classList.add(
        "reschedule-times"
    );


    let newSelectedTime =
        null;


    const saveButton =
        document.createElement(
            "button"
        );


    saveButton.type =
        "button";

    saveButton.classList.add(
        "save-reschedule-button"
    );

    saveButton.textContent =
        "Salvar alteração";

    saveButton.disabled =
        true;


    const closeButton =
        document.createElement(
            "button"
        );


    closeButton.type =
        "button";

    closeButton.classList.add(
        "close-reschedule-button"
    );

    closeButton.textContent =
        "Fechar";


    closeButton.addEventListener(
        "click",
        function () {

            panel.remove();

        }
    );


    const panelActions =
        document.createElement(
            "div"
        );


    panelActions.classList.add(
        "reschedule-actions"
    );


    panelActions.appendChild(
        saveButton
    );

    panelActions.appendChild(
        closeButton
    );


    async function loadRescheduleTimes() {

        const newDate =
            newDateInput.value;


        timesContainer.innerHTML =
            "";

        message.textContent =
            "";

        newSelectedTime =
            null;

        saveButton.disabled =
            true;


        if (!newDate) {

            message.textContent =
                "Escolha uma nova data.";

            message.className =
                "reschedule-message error";

            return;
        }


        try {

            searchButton.disabled =
                true;

            searchButton.textContent =
                "Buscando...";


            const response =
                await fetch(

                    `/available?date=${encodeURIComponent(newDate)}&specialty=${encodeURIComponent(appointment.specialty)}&exclude_id=${appointment.id}`

                );


            const data =
                await response.json();


            if (!response.ok) {

                message.textContent =
                    data.error ||
                    data.message ||
                    "Não foi possível consultar os horários.";

                message.className =
                    "reschedule-message error";

                return;
            }


            if (
                !data.available ||
                data.available.length === 0
            ) {

                message.textContent =
                    "Não existem horários disponíveis.";

                message.className =
                    "reschedule-message error";

                return;
            }


            message.textContent =
                "Selecione o novo horário.";

            message.className =
                "reschedule-message success";


            data.available.forEach(
                function (time) {

                    const timeButton =
                        document.createElement(
                            "button"
                        );


                    timeButton.type =
                        "button";

                    timeButton.classList.add(
                        "reschedule-time-button"
                    );

                    timeButton.textContent =
                        time;


                    timeButton.addEventListener(
                        "click",
                        function () {

                            timesContainer
                                .querySelectorAll(
                                    ".reschedule-time-button"
                                )
                                .forEach(
                                    function (button) {

                                        button.classList.remove(
                                            "selected"
                                        );

                                    }
                                );


                            timeButton.classList.add(
                                "selected"
                            );


                            newSelectedTime =
                                time;


                            saveButton.disabled =
                                false;

                        }
                    );


                    timesContainer.appendChild(
                        timeButton
                    );

                }
            );


        } catch (error) {

            console.error(
                error
            );


            message.textContent =
                "Erro ao consultar horários.";

            message.className =
                "reschedule-message error";


        } finally {

            searchButton.disabled =
                false;

            searchButton.textContent =
                "Ver horários";

        }

    }


    searchButton.addEventListener(
        "click",
        loadRescheduleTimes
    );


    saveButton.addEventListener(
        "click",
        async function () {

            if (
                !newDateInput.value ||
                !newSelectedTime
            ) {

                return;

            }


            try {

                saveButton.disabled =
                    true;

                saveButton.textContent =
                    "Salvando...";


                const response =
                    await fetch(
                        `/appointments/${appointment.id}`,
                        {

                            method:
                                "PUT",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body:
                                JSON.stringify({

                                    specialty:
                                        appointment.specialty,

                                    date:
                                        newDateInput.value,

                                    time:
                                        newSelectedTime

                                })

                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    message.textContent =
                        data.error ||
                        "Não foi possível reagendar.";

                    message.className =
                        "reschedule-message error";

                    return;
                }


                alert(
                    "Agendamento alterado com sucesso!"
                );


                await loadAppointments();


                await updateAvailableTimes();


            } catch (error) {

                console.error(
                    error
                );


                message.textContent =
                    "Erro de comunicação com o servidor.";

                message.className =
                    "reschedule-message error";


            } finally {

                saveButton.textContent =
                    "Salvar alteração";

            }

        }
    );


    panel.appendChild(
        heading
    );

    panel.appendChild(
        dateGroup
    );

    panel.appendChild(
        searchButton
    );

    panel.appendChild(
        message
    );

    panel.appendChild(
        timesContainer
    );

    panel.appendChild(
        panelActions
    );


    card.appendChild(
        panel
    );


    loadRescheduleTimes();

}


// ========================================
// CANCELAR
// ========================================

async function cancelAppointment(
    appointment
) {

    const confirmed =
        confirm(

            `Deseja realmente cancelar a consulta de ${appointment.patient_name} em ${formatDate(appointment.date)} às ${appointment.time}?`

        );


    if (!confirmed) {

        return;

    }


    try {

        const response =
            await fetch(
                `/appointments/${appointment.id}`,
                {
                    method:
                        "DELETE"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            alert(
                data.error ||
                "Não foi possível cancelar."
            );

            return;
        }


        alert(
            "Agendamento cancelado com sucesso."
        );


        await loadAppointments();

        await updateAvailableTimes();


    } catch (error) {

        console.error(
            error
        );


        alert(
            "Erro de comunicação com o servidor."
        );

    }

}


// ========================================
// DETALHES
// ========================================

function createDetail(
    label,
    value
) {

    const paragraph =
        document.createElement(
            "p"
        );


    const strong =
        document.createElement(
            "strong"
        );


    strong.textContent =
        `${label}: `;


    paragraph.appendChild(
        strong
    );


    paragraph.appendChild(
        document.createTextNode(
            value
        )
    );


    return paragraph;

}


// ========================================
// DATA
// ========================================

function formatDate(
    dateString
) {

    const parts =
        dateString.split(
            "-"
        );


    if (
        parts.length !== 3
    ) {

        return dateString;

    }


    return (
        `${parts[2]}/` +
        `${parts[1]}/` +
        `${parts[0]}`
    );

}


// ========================================
// MENSAGENS
// ========================================

function showMessage(
    element,
    message,
    type
) {

    element.textContent =
        message;

    element.className =
        "message";

    element.classList.add(
        type
    );

}


function clearMessage(
    element
) {

    element.textContent =
        "";

    element.className =
        "message";

}