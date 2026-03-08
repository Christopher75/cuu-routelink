function calculateAge(dob) {
    var today = new Date();
    // HTML5 date input returns yyyy-mm-dd
    var parts = dob.split('-');
    var birthDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
    var age = today.getFullYear() - birthDate.getFullYear();
    var monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    return age;
}

function updateAge() {
    var dobInput = document.getElementById('id_dob');
    var ageInput = document.getElementById('id_age');
    if (dobInput && ageInput && dobInput.value) {
        ageInput.value = calculateAge(dobInput.value);
    } else if (ageInput) {
        ageInput.value = '';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    var dobInput = document.getElementById('id_dob');
    if (dobInput) {
        dobInput.addEventListener('change', updateAge);
        dobInput.addEventListener('input', updateAge);
        // Run on load in case the field is pre-filled
        if (dobInput.value) updateAge();
    }
});
