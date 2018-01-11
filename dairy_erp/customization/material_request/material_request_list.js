frappe.listview_settings['Material Request'] = {
	add_fields: ["material_request_type", "status", "per_ordered","per_delivered","per_closed"],
	get_indicator: function(doc) {
		if(doc.status=="Stopped") {
			return [__("Stopped"), "red", "status,=,Stopped"];
		}else if(doc.docstatus==1 && flt(doc.per_ordered, 2) == 0 && flt(doc.per_delivered, 2) == 100) {
			return [__("Delivered"), "green", "per_ordered,=,0|per_delivered,=,100"];
		} else if(doc.docstatus==1 && flt(doc.per_ordered, 2) == 0) {
			return [__("Pending"), "orange", "per_ordered,=,0"];
		}  else if(doc.docstatus==1 && flt(doc.per_ordered, 2) < 100) {
			return [__("Partially ordered"), "yellow", "per_ordered,<,100"];
		} 
		else if(doc.material_request_type == "Purchase" && doc.docstatus==1 && flt(doc.per_closed, 2) == 100 && flt(doc.per_ordered, 2) == 100) {
			return [__("Closed"), "green", "per_closed,=,100|per_ordered,=,100"];
		}
		else if(doc.material_request_type == "Purchase" && doc.docstatus==1 && flt(doc.per_delivered, 2) == 100) {
			return [__("Delivered"), "green", "per_delivered,=,100"];
		}
		else if(doc.material_request_type == "Purchase" && doc.docstatus==1 && flt(doc.per_ordered, 2) == 100 && flt(doc.per_delivered, 2) == 0) {
			return [__("Ordered"), "green", "per_ordered,=,100"];
		}
		else if(doc.material_request_type == "Purchase" && doc.docstatus==1 && flt(doc.per_delivered,2) < 100 && flt(doc.per_ordered, 2) == 100) {
			return [__("Partially Delivered"), "green", "per_delivered,<,100|per_ordered,=,100"];
		}
		else if(doc.docstatus==1 && flt(doc.per_ordered, 2) == 100) {
			if (doc.material_request_type == "Purchase") {
				return [__("Ordered"), "green", "per_ordered,=,100"];
			} else if (doc.material_request_type == "Material Transfer") {
				return [__("Transfered"), "green", "per_ordered,=,100"];
			} else if (doc.material_request_type == "Material Issue") {
				return [__("Issued"), "green", "per_ordered,=,100"];
			}
		}
	}
};
