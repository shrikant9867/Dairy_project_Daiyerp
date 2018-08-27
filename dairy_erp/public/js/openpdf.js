
open_pdf = function(html) {
        //Create a form to place the HTML content
        var formData = new FormData();

        //Push the HTML content into an element
        formData.append("html", html);
        // formData.append("orientation", orientation);
        var blob = new Blob([], { type: "text/xml"});
        //formData.append("webmasterfile", blob);
        formData.append("blob", blob);

        var xhr = new XMLHttpRequest();
        xhr.open("POST", '/api/method/frappe.utils.print_format.report_to_pdf');
        xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);
        xhr.responseType = "arraybuffer";

        xhr.onload = function(success) {
            if (this.status === 200) {
                var blob = new Blob([success.currentTarget.response], {type: "application/pdf"});
                var objectUrl = URL.createObjectURL(blob);

                //Open report in a new window
                window.open(objectUrl);
            }
        };
        xhr.send(formData);
    }