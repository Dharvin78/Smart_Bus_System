document.addEventListener("DOMContentLoaded", function () {

    const input = document.getElementById("id_photo");
    const preview = document.getElementById("previewImage");

    if (input && preview) {

        input.addEventListener("change", function () {

            const file = this.files[0];

            if (file) {

                preview.src = URL.createObjectURL(file);
                preview.style.display = "block";

            }

        });

    }

});