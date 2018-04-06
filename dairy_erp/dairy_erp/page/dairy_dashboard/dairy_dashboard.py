from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from dairy_erp.dairy_erp.page.vlcc_dashboard.vlcc_dashboard import get_total_counts


@frappe.whitelist()
def get_data():
    address = frappe.db.sql("""select name,address_type,pincode,address_line1,state,address_line2,city,country,email_id,phone,fax 
                                from `tabAddress`""",as_dict=1)
    camp_off = 0
    plant = 0 
    cc = 0
    if address:
        for addr in address:
            if addr.get('address_type') == 'Head Office':
                office_addr = address_manipulation(addr)
                addr.update({"office_addr":office_addr})
                final_addr = ""
            else:
                if addr.get('address_type') == "Camp Office":
                    if camp_off != 2:
                        office_addr = address_manipulation(addr)
                        addr.update({"office_addr":office_addr})
                        final_addr = ""
                        camp_off += 1
                if addr.get('address_type') == "Plant":
                    if plant != 2:
                        office_addr = address_manipulation(addr)
                        addr.update({"office_addr":office_addr})
                        final_addr = ""
                        plant += 1
                if addr.get('address_type') == "Chilling Centre":
                    if cc != 2:
                        office_addr = address_manipulation(addr)
                        addr.update({"office_addr":office_addr})
                        final_addr = ""
                        cc += 1
        vlcc = get_vlcc_data()
        supplier = get_supplier_data()
        vlcc_name = frappe.get_value("User", frappe.session.user, "company")
        return {"addr":address,"vlcc":vlcc,"supplier":supplier, "total_summery": get_total_counts("Vlcc Milk Collection Record")}

def address_manipulation(addr):
    final_addr = ""
    if addr.get('address_line1'):
        final_addr += addr.get('address_line1') + "<br>"
    if addr.get('address_line2'):
        final_addr += addr.get('address_line2') + "<br>"
    if addr.get('city'):
        final_addr += addr.get('city') + "<br>" 
    if addr.get('state'):
        final_addr += addr.get('state') + "<br>" 
    if addr.get('pincode'):
        final_addr += addr.get('pincode') + "<br>" 
    if addr.get('country'):
        final_addr += addr.get('country') + "<br>" 
    if addr.get('phone'):
        final_addr += addr.get('phone') + "<br>"
    if addr.get('fax'):
        final_addr += addr.get('fax') + "<br>"
    if addr.get('email_id'):
        final_addr += addr.get('email_id') + "<br>"
    return final_addr

def get_vlcc_data():
    return frappe.db.sql("""select name,address_display as addr from `tabVillage Level Collection Centre` limit 2""",as_dict=1)

def get_supplier_data():
    address = frappe.db.sql("""select a.name,a.address_type,a.pincode,a.address_line1,a.state,a.address_line2,a.city,a.country,a.email_id,a.phone,a.fax, s.name as supplier,s.supplier_type 
                               from `tabSupplier` s  
                               left join `tabDynamic Link` d on d.link_name = s.name 
                               left join `tabAddress` a on d.parent = a.name 
                               where s.supplier_type = 'Dairy Local' limit 2""",as_dict=1)
    if address:
        for addr in address:
            office_addr = address_manipulation(addr)
            addr.update({"addr":office_addr})
            final_addr = ""
        return address