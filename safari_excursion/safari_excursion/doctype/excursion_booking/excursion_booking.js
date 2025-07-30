// ~/frappe-bench/apps/safari_excursion/safari_excursion/safari_excursion/doctype/excursion_booking/excursion_booking.js

frappe.ui.form.on('Excursion Booking', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.docstatus === 1) {
            add_custom_buttons(frm);
        }
        
        // Show park fee information if available
        if (frm.doc.excursion_package) {
            show_park_fee_info(frm);
        }
        
        // Update total guests when adult/child count changes
        update_total_guests(frm);
        
        // Handle pickup type display
        handle_pickup_type_display(frm);
        
        // Show pickup schedule if individual pickups
        if (frm.doc.pickup_type === 'Individual Hotel Pickups') {
            show_pickup_management_buttons(frm);
        }
    },
    
    onload: function(frm) {
        // Set default pickup type
        if (!frm.doc.pickup_type) {
            frm.set_value('pickup_type', 'Central Pickup Point');
        }
    },
    
    excursion_package: function(frm) {
        if (frm.doc.excursion_package) {
            // Fetch package details and set defaults
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Excursion Package',
                    name: frm.doc.excursion_package
                },
                callback: function(r) {
                    if (r.message) {
                        const package_doc = r.message;
                        
                        // Set duration
                        frm.set_value('duration_hours', package_doc.duration_hours);
                        
                        // Set default departure times if available
                        if (package_doc.departure_times && package_doc.departure_times.length > 0) {
                            frm.set_value('departure_time', package_doc.departure_times[0].departure_time);
                        }
                        
                        // Calculate and show pricing
                        calculate_pricing(frm);
                        
                        // Show park fee information
                        show_park_fee_info(frm);
                        
                        // Set default pickup type based on package
                        if (package_doc.pickup_locations && package_doc.pickup_locations.length > 0) {
                            frm.set_value('pickup_type', 'Central Pickup Point');
                        }
                    }
                }
            });
        }
    },
    
    pickup_type: function(frm) {
        handle_pickup_type_change(frm);
    },
    
    adult_count: function(frm) {
        update_total_guests(frm);
        calculate_pricing(frm);
    },
    
    child_count: function(frm) {
        update_total_guests(frm);
        calculate_pricing(frm);
    },
    
    excursion_date: function(frm) {
        if (frm.doc.excursion_package && frm.doc.adult_count) {
            calculate_pricing(frm);
        }
    },
    
    departure_time: function(frm) {
        if (frm.doc.excursion_package && frm.doc.adult_count) {
            calculate_pricing(frm);
        }
        
        // Update pickup times if individual pickups
        if (frm.doc.pickup_type === 'Individual Hotel Pickups' && frm.doc.guest_pickups) {
            update_pickup_times_from_departure(frm);
        }
    },
    
    total_guests: function(frm) {
        // Regenerate pickup schedule if pickup type is individual and total guests changed
        if (frm.doc.pickup_type === 'Individual Hotel Pickups' && frm.doc.total_guests > 0) {
            if (frm.doc.guest_pickups && frm.doc.guest_pickups.length !== frm.doc.total_guests) {
                frappe.confirm(
                    __('Total guests has changed. Do you want to regenerate the pickup schedule?'),
                    function() {
                        create_pickup_schedule(frm);
                    }
                );
            }
        }
    }
});

function handle_pickup_type_display(frm) {
    // Show/hide fields based on pickup type
    if (frm.doc.pickup_type === 'Individual Hotel Pickups') {
        frm.set_df_property('pickup_location', 'hidden', 1);
        frm.set_df_property('pickup_time', 'hidden', 1);
        frm.set_df_property('guest_pickups', 'hidden', 0);
        frm.set_df_property('pickup_location', 'reqd', 0);
        frm.set_df_property('pickup_time', 'reqd', 0);
    } else if (frm.doc.pickup_type === 'Central Pickup Point') {
        frm.set_df_property('pickup_location', 'hidden', 0);
        frm.set_df_property('pickup_time', 'hidden', 0);
        frm.set_df_property('guest_pickups', 'hidden', 1);
        frm.set_df_property('pickup_location', 'reqd', 1);
        frm.set_df_property('pickup_time', 'reqd', 1);
    } else {
        // Mixed pickup - show both
        frm.set_df_property('pickup_location', 'hidden', 0);
        frm.set_df_property('pickup_time', 'hidden', 0);
        frm.set_df_property('guest_pickups', 'hidden', 0);
    }
}

function handle_pickup_type_change(frm) {
    handle_pickup_type_display(frm);
    
    if (frm.doc.pickup_type === 'Individual Hotel Pickups') {
        // Clear central pickup fields
        frm.set_value('pickup_location', '');
        frm.set_value('pickup_time', '');
        
        // Create pickup schedule if guests are available
        if (frm.doc.total_guests > 0) {
            frappe.confirm(
                __('Do you want to create an individual pickup schedule for all guests?'),
                function() {
                    create_pickup_schedule(frm);
                }
            );
        }
    } else if (frm.doc.pickup_type === 'Central Pickup Point') {
        // Clear individual pickup schedule
        frm.clear_table('guest_pickups');
        frm.refresh_field('guest_pickups');
        
        // Set default pickup time if departure time is set
        if (frm.doc.departure_time && !frm.doc.pickup_time) {
            let departure = new Date('2000-01-01 ' + frm.doc.departure_time);
            departure.setMinutes(departure.getMinutes() - 30); // 30 minutes before departure
            frm.set_value('pickup_time', departure.toTimeString().substr(0, 8));
        }
    }
}

function add_custom_buttons(frm) {
    // Send reminder button
    if (frm.doc.customer_email && !frm.doc.reminder_sent) {
        frm.add_custom_button(__('Send Reminder'), function() {
            frappe.call({
                method: 'send_reminder_notification',
                doc: frm.doc,
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__('Reminder sent successfully'));
                        frm.reload_doc();
                    }
                }
            });
        }, __('Communications'));
    }
    
    // Assign Guide/Vehicle button
    if (frm.doc.booking_status === 'Confirmed') {
        frm.add_custom_button(__('Assign Resources'), function() {
            show_assignment_dialog(frm);
        }, __('Operations'));
    }
    
    // View Park Fees button
    if (frm.doc.park_booking) {
        frm.add_custom_button(__('View Park Fees'), function() {
            show_park_fee_breakdown(frm);
        }, __('Parks'));
    }
    
    // Update Pricing button
    frm.add_custom_button(__('Recalculate Pricing'), function() {
        calculate_pricing(frm, true);
    }, __('Pricing'));
    
    // Pickup management buttons
    if (frm.doc.pickup_type === 'Individual Hotel Pickups') {
        show_pickup_management_buttons(frm);
    }
    
    // Driver notification button
    if (frm.doc.assigned_guide) {
        frm.add_custom_button(__('Send Driver Schedule'), function() {
            send_driver_schedule(frm);
        }, __('Communications'));
    }
}

function show_pickup_management_buttons(frm) {
    // Add pickup schedule management buttons
    frm.add_custom_button(__('Create Pickup Schedule'), function() {
        create_pickup_schedule(frm);
    }, __('Pickup Management'));
    
    frm.add_custom_button(__('Send Pickup Confirmations'), function() {
        send_pickup_confirmations(frm);
    }, __('Pickup Management'));
    
    frm.add_custom_button(__('Driver Pickup Schedule'), function() {
        show_driver_pickup_schedule(frm);
    }, __('Pickup Management'));
    
    frm.add_custom_button(__('Optimize Route'), function() {
        optimize_pickup_route(frm);
    }, __('Pickup Management'));
    
    frm.add_custom_button(__('Send Pickup Reminders'), function() {
        send_pickup_reminders(frm);
    }, __('Pickup Management'));
}

function create_pickup_schedule(frm) {
    if (!frm.doc.total_guests || frm.doc.total_guests === 0) {
        frappe.msgprint(__('Please specify the number of guests first'));
        return;
    }
    
    frappe.call({
        method: 'safari_excursion.utils.multiple_pickup_transport.create_pickup_schedule',
        args: {
            excursion_booking: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.msgprint(r.message.message);
                frm.reload_doc();
            } else {
                frappe.msgprint(__('Failed to create pickup schedule: ') + (r.message ? r.message.message : 'Unknown error'));
            }
        }
    });
}

function send_pickup_confirmations(frm) {
    if (!frm.doc.guest_pickups || frm.doc.guest_pickups.length === 0) {
        frappe.msgprint(__('No pickup schedule found. Please create pickup schedule first.'));
        return;
    }
    
    frappe.confirm(
        __('Send pickup confirmation emails to all guests?'),
        function() {
            frappe.call({
                method: 'safari_excursion.utils.multiple_pickup_transport.send_individual_pickup_confirmations',
                args: {
                    excursion_booking: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.msgprint(__('Pickup confirmations sent successfully'));
                    } else {
                        frappe.msgprint(__('Failed to send confirmations'));
                    }
                }
            });
        }
    );
}

function show_driver_pickup_schedule(frm) {
    frappe.call({
        method: 'safari_excursion.utils.multiple_pickup_transport.generate_driver_pickup_schedule',
        args: {
            excursion_booking: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let dialog = new frappe.ui.Dialog({
                    title: __('Driver Pickup Schedule'),
                    size: 'extra-large',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'schedule_html',
                            options: r.message
                        }
                    ],
                    primary_action_label: __('Print Schedule'),
                    primary_action: function() {
                        print_pickup_schedule(r.message, frm.doc.booking_number);
                    },
                    secondary_action_label: __('Send to Driver'),
                    secondary_action: function() {
                        send_driver_schedule(frm);
                        dialog.hide();
                    }
                });
                dialog.show();
            }
        }
    });
}

function print_pickup_schedule(schedule_html, booking_number) {
    let print_window = window.open('', '_blank');
    print_window.document.write(`
        <html>
            <head>
                <title>Pickup Schedule - ${booking_number}</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                        line-height: 1.4;
                    }
                    table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        margin: 10px 0; 
                        page-break-inside: avoid;
                    }
                    th, td { 
                        border: 1px solid #ddd; 
                        padding: 8px; 
                        text-align: left; 
                        vertical-align: top;
                    }
                    th { 
                        background-color: #f2f2f2; 
                        font-weight: bold;
                    }
                    h3 { 
                        color: #333; 
                        border-bottom: 2px solid #ddd;
                        padding-bottom: 5px;
                    }
                    .important {
                        background-color: #fff3cd;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px 0;
                    }
                    @media print { 
                        body { margin: 0; }
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                ${schedule_html}
                <div style="margin-top: 30px; text-align: center; color: #666; font-size: 12px;">
                    Printed on ${new Date().toLocaleString()}
                </div>
            </body>
        </html>
    `);
    print_window.document.close();
    print_window.print();
}

function send_driver_schedule(frm) {
    if (!frm.doc.assigned_guide) {
        frappe.msgprint(__('Please assign a guide first'));
        return;
    }
    
    frappe.call({
        method: 'safari_excursion.utils.driver_pickup_notifications.send_driver_pickup_schedule_now',
        args: {
            excursion_booking: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.msgprint(__('Pickup schedule sent to driver successfully'));
            } else {
                frappe.msgprint(__('Failed to send schedule: ') + (r.message ? r.message.message : 'Unknown error'));
            }
        }
    });
}

function optimize_pickup_route(frm) {
    if (!frm.doc.guest_pickups || frm.doc.guest_pickups.length === 0) {
        frappe.msgprint(__('No pickup schedule found. Please create pickup schedule first.'));
        return;
    }
    
    frappe.confirm(
        __('This will reorder the pickup sequence for optimal routing. Continue?'),
        function() {
            frappe.call({
                method: 'safari_excursion.utils.multiple_pickup_transport.optimize_pickup_route',
                args: {
                    excursion_booking: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.msgprint(__('Pickup route optimized successfully'));
                        frm.reload_doc();
                    } else {
                        frappe.msgprint(__('Failed to optimize route'));
                    }
                }
            });
        }
    );
}

function send_pickup_reminders(frm) {
    frappe.call({
        method: 'safari_excursion.utils.driver_pickup_notifications.send_pickup_reminders_now',
        args: {
            excursion_booking: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                frappe.msgprint(r.message.message);
            } else {
                frappe.msgprint(__('Failed to send reminders: ') + (r.message ? r.message.message : 'Unknown error'));
            }
        }
    });
}

function update_pickup_times_from_departure(frm) {
    // Recalculate pickup times based on new departure time
    if (!frm.doc.guest_pickups || frm.doc.guest_pickups.length === 0) {
        return;
    }
    
    let departure_time = frm.doc.departure_time;
    let pickup_buffer = 30; // 30 minutes buffer before departure
    let travel_between_hotels = 15; // 15 minutes between hotels
    let pickup_duration = 5; // 5 minutes per pickup
    
    // Calculate total pickup time
    let total_pickup_time = frm.doc.guest_pickups.length * pickup_duration + 
                           (frm.doc.guest_pickups.length - 1) * travel_between_hotels;
    
    // Calculate first pickup time
    let departure = new Date('2000-01-01 ' + departure_time);
    let first_pickup = new Date(departure.getTime() - (total_pickup_time + pickup_buffer) * 60000);
    
    // Update all pickup times
    frm.doc.guest_pickups.forEach(function(pickup, index) {
        let pickup_time = new Date(first_pickup.getTime() + index * (pickup_duration + travel_between_hotels) * 60000);
        pickup.estimated_pickup_time = pickup_time.toTimeString().substr(0, 8);
    });
    
    frm.refresh_field('guest_pickups');
}

function update_total_guests(frm) {
    const adult_count = frm.doc.adult_count || 0;
    const child_count = frm.doc.child_count || 0;
    frm.set_value('total_guests', adult_count + child_count);
}

function calculate_pricing(frm, force_recalculate = false) {
    if (!frm.doc.excursion_package || !frm.doc.adult_count) {
        return;
    }
    
    frappe.call({
        method: 'safari_excursion.utils.pricing_calculator.get_excursion_pricing_preview',
        args: {
            excursion_package: frm.doc.excursion_package,
            adult_count: frm.doc.adult_count,
            child_count: frm.doc.child_count || 0,
            excursion_date: frm.doc.excursion_date,
            departure_time: frm.doc.departure_time
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                const pricing = r.message.pricing;
                
                if (force_recalculate || frm.doc.__islocal) {
                    frm.set_value('base_amount', pricing.base_amount);
                    frm.set_value('child_discount', pricing.child_discount);
                    frm.set_value('group_discount', pricing.group_discount);
                    frm.set_value('additional_charges', pricing.additional_charges);
                    frm.set_value('total_amount', pricing.total_amount);
                    frm.set_value('balance_due', pricing.total_amount - (frm.doc.deposit_amount || 0));
                }
                
                // Show pricing breakdown
                show_pricing_breakdown(frm, pricing);
            }
        }
    });
}

function show_pricing_breakdown(frm, pricing) {
    const breakdown_html = `
        <div class="pricing-breakdown" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
            <h6>Pricing Breakdown</h6>
            <table class="table table-sm">
                <tr><td>Base Amount</td><td class="text-right">$${pricing.base_amount.toFixed(2)}</td></tr>
                ${pricing.child_discount > 0 ? `<tr><td>Child Discount</td><td class="text-right text-success">-$${pricing.child_discount.toFixed(2)}</td></tr>` : ''}
                ${pricing.group_discount > 0 ? `<tr><td>Group Discount</td><td class="text-right text-success">-$${pricing.group_discount.toFixed(2)}</td></tr>` : ''}
                ${pricing.additional_charges > 0 ? `<tr><td>Additional Charges</td><td class="text-right">+$${pricing.additional_charges.toFixed(2)}</td></tr>` : ''}
                <tr class="font-weight-bold"><td>Total Amount</td><td class="text-right">$${pricing.total_amount.toFixed(2)}</td></tr>
            </table>
        </div>
    `;
    
    // Find or create breakdown section
    let breakdown_section = frm.fields_dict.pricing_section.$wrapper.find('.pricing-breakdown');
    if (breakdown_section.length) {
        breakdown_section.replaceWith(breakdown_html);
    } else {
        frm.fields_dict.pricing_section.$wrapper.append(breakdown_html);
    }
}

function show_park_fee_info(frm) {
    if (!frm.doc.excursion_package) return;
    
    frappe.call({
        method: 'safari_excursion.utils.parks_integration.get_excursion_park_fees',
        args: {
            excursion_booking: frm.doc.name || 'preview'
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                const park_fees = r.message.park_fees;
                
                if (park_fees.total_fees > 0) {
                    show_park_fee_summary(frm, park_fees);
                }
            }
        }
    });
}

function show_park_fee_summary(frm, park_fees) {
    let park_info_html = `
        <div class="park-fees-info" style="margin-top: 10px; padding: 10px; background: #e8f5e8; border-radius: 4px; border-left: 4px solid #28a745;">
            <h6><i class="fa fa-tree"></i> Park Fees Included</h6>
            <p class="mb-2"><strong>Total Park Fees: $${park_fees.total_fees.toFixed(2)}</strong></p>
    `;
    
    if (park_fees.fee_breakdown.length > 0) {
        park_info_html += '<div class="park-breakdown">';
        park_fees.fee_breakdown.forEach(park => {
            park_info_html += `
                <div class="mb-2">
                    <strong>${park.park_name}</strong><br>
                    <small>
                        Adults: $${park.adult_fee.toFixed(2)} | 
                        Children: $${park.child_fee.toFixed(2)}
                        ${park.vehicle_fee > 0 ? ` | Vehicle: $${park.vehicle_fee.toFixed(2)}` : ''}
                    </small>
                </div>
            `;
        });
        park_info_html += '</div>';
    }
    
    park_info_html += '</div>';
    
    // Find or create park info section
    let park_section = frm.fields_dict.excursion_details_section.$wrapper.find('.park-fees-info');
    if (park_section.length) {
        park_section.replaceWith(park_info_html);
    } else {
        frm.fields_dict.excursion_details_section.$wrapper.append(park_info_html);
    }
}

function show_park_fee_breakdown(frm) {
    frappe.call({
        method: 'safari_excursion.utils.parks_integration.get_excursion_park_fees',
        args: {
            excursion_booking: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.status === 'success') {
                const park_fees = r.message.park_fees;
                
                let content = '<h4>Park Fee Breakdown</h4>';
                
                if (park_fees.fee_breakdown.length > 0) {
                    content += '<table class="table table-bordered">';
                    content += '<thead><tr><th>Park</th><th>Adults</th><th>Children</th><th>Vehicle</th><th>Total</th></tr></thead>';
                    content += '<tbody>';
                    
                    park_fees.fee_breakdown.forEach(park => {
                        content += `
                            <tr>
                                <td>${park.park_name}</td>
                                <td>$${park.adult_fee.toFixed(2)}</td>
                                <td>$${park.child_fee.toFixed(2)}</td>
                                <td>$${park.vehicle_fee.toFixed(2)}</td>
                                <td><strong>$${park.total_fee.toFixed(2)}</strong></td>
                            </tr>
                        `;
                    });
                    
                    content += '</tbody>';
                    content += `<tfoot><tr><th colspan="4">Grand Total</th><th>$${park_fees.total_fees.toFixed(2)}</th></tr></tfoot>`;
                    content += '</table>';
                } else {
                    content += '<p>No park fees applicable for this excursion.</p>';
                }
                
                frappe.msgprint({
                    title: __('Park Fee Details'),
                    message: content,
                    wide: true
                });
            }
        }
    });
}

function show_assignment_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('Assign Guide and Vehicle'),
        fields: [
            {
                label: __('Available Guides'),
                fieldname: 'guide',
                fieldtype: 'Link',
                options: 'Safari Guide',
                get_query: function() {
                    return {
                        filters: {
                            'is_active': 1,
                            'availability_status': 'Available'
                        }
                    };
                }
            },
            {
                label: __('Available Vehicles'),
                fieldname: 'vehicle',
                fieldtype: 'Link',
                options: 'Vehicle',
                get_query: function() {
                    return {
                        filters: {
                            'status': 'Available',
                            'capacity': ['>=', frm.doc.total_guests]
                        }
                    };
                }
            }
        ],
        primary_action_label: __('Assign'),
        primary_action: function(values) {
            if (values.guide || values.vehicle) {
                frappe.call({
                    method: 'assign_guide_and_vehicle',
                    doc: frm.doc,
                    args: {
                        guide: values.guide,
                        vehicle: values.vehicle
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Resources assigned successfully'));
                            frm.reload_doc();
                            dialog.hide();
                        }
                    }
                });
            } else {
                frappe.msgprint(__('Please select at least one resource to assign'));
            }
        }
    });
    
    dialog.show();
}

// Child table events for pickup schedule
frappe.ui.form.on('Excursion Guest Pickup', {
    pickup_status: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        // Update pickup status in real-time
        if (row.pickup_status && frm.doc.name) {
            frappe.call({
                method: 'safari_excursion.utils.multiple_pickup_transport.update_pickup_status',
                args: {
                    excursion_booking: frm.doc.name,
                    pickup_order: row.pickup_order,
                    status: row.pickup_status,
                    notes: row.special_notes
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Pickup status updated'),
                            indicator: 'green'
                        });
                        
                        // Update visual indicators
                        update_pickup_status_indicators(frm);
                    }
                }
            });
        }
    },
    
    pickup_location_name: function(frm, cdt, cdn) {
        // Auto-generate meeting instructions based on location type
        let row = locals[cdt][cdn];
        if (row.pickup_location_name && row.pickup_location_type) {
            let instructions = generate_meeting_instructions(row.pickup_location_type);
            frappe.model.set_value(cdt, cdn, 'meeting_instructions', instructions);
        }
    }
});

function update_pickup_status_indicators(frm) {
    // Add visual indicators for pickup progress
    if (!frm.doc.guest_pickups) return;
    
    let completed = frm.doc.guest_pickups.filter(p => p.pickup_status === 'Completed').length;
    let total = frm.doc.guest_pickups.length;
    
    if (completed === total && total > 0) {
        frm.dashboard.add_indicator(__('All Pickups Completed'), 'green');
    } else if (completed > 0) {
        frm.dashboard.add_indicator(__(`${completed}/${total} Pickups Completed`), 'orange');
    }
}

function generate_meeting_instructions(location_type) {
    const instructions = {
        'Hotel': 'Meet at hotel main lobby/reception. Look for safari vehicle with company branding.',
        'Resort': 'Meet at main reception area. Driver will contact you upon arrival.',
        'Airbnb': 'Meet at main entrance or lobby area. Please be ready and waiting.',
        'Private Residence': 'Meet at main gate or entrance. Driver will call upon arrival.',
        'Lodge': 'Meet at main reception/lobby area.',
        'Guest House': 'Meet at reception or main entrance.',
        'Hostel': 'Meet at reception desk. Driver will ask for you by name.',
        'Other': 'Meet at main entrance. Driver will call you 5 minutes before arrival.'
    };
    
    return instructions[location_type] || instructions['Other'];
}

// Additional utility functions for pickup management
function validate_pickup_schedule(frm) {
    if (!frm.doc.guest_pickups || frm.doc.guest_pickups.length === 0) {
        frappe.msgprint(__('No pickup schedule found'));
        return false;
    }
    
    // Check for missing required fields
    let missing_fields = [];
    frm.doc.guest_pickups.forEach(function(pickup, index) {
        if (!pickup.guest_name) missing_fields.push(`Row ${index + 1}: Guest Name`);
        if (!pickup.pickup_location_name) missing_fields.push(`Row ${index + 1}: Location Name`);
        if (!pickup.pickup_address) missing_fields.push(`Row ${index + 1}: Address`);
        if (!pickup.contact_phone) missing_fields.push(`Row ${index + 1}: Contact Phone`);
        if (!pickup.estimated_pickup_time) missing_fields.push(`Row ${index + 1}: Pickup Time`);
    });
    
    if (missing_fields.length > 0) {
        frappe.msgprint({
            title: __('Incomplete Pickup Schedule'),
            message: __('Please fill in the following required fields:<br>') + missing_fields.join('<br>'),
            indicator: 'red'
        });
        return false;
    }
    
    return true;
}

function export_pickup_schedule(frm) {
    if (!validate_pickup_schedule(frm)) return;
    
    // Create CSV export of pickup schedule
    let csv_data = [
        ['Order', 'Time', 'Guest Name', 'Location', 'Address', 'Phone', 'Instructions']
    ];
    
    frm.doc.guest_pickups.forEach(function(pickup) {
        csv_data.push([
            pickup.pickup_order,
            pickup.estimated_pickup_time,
            pickup.guest_name,
            pickup.pickup_location_name,
            pickup.pickup_address,
            pickup.contact_phone,
            pickup.meeting_instructions || ''
        ]);
    });
    
    // Convert to CSV string
    let csv_string = csv_data.map(row => 
        row.map(field => `"${field}"`).join(',')
    ).join('\n');
    
    // Download CSV file
    let blob = new Blob([csv_string], { type: 'text/csv' });
    let url = window.URL.createObjectURL(blob);
    let a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `pickup_schedule_${frm.doc.booking_number}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    frappe.msgprint(__('Pickup schedule exported successfully'));
}

// Real-time pickup tracking functions
function start_pickup_tracking(frm) {
    if (!frm.doc.guest_pickups || frm.doc.guest_pickups.length === 0) {
        frappe.msgprint(__('No pickup schedule available'));
        return;
    }
    
    // Create pickup tracking interface
    let dialog = new frappe.ui.Dialog({
        title: __('Live Pickup Tracking'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'tracking_html',
                options: generate_pickup_tracking_html(frm)
            }
        ],
        primary_action_label: __('Refresh'),
        primary_action: function() {
            // Reload and update tracking display
            dialog.fields_dict.tracking_html.$wrapper.html(generate_pickup_tracking_html(frm));
        }
    });
    
    dialog.show();
    
    // Auto-refresh every 30 seconds
    dialog.auto_refresh = setInterval(function() {
        if (dialog.display) {
            dialog.fields_dict.tracking_html.$wrapper.html(generate_pickup_tracking_html(frm));
        } else {
            clearInterval(dialog.auto_refresh);
        }
    }, 30000);
}

function generate_pickup_tracking_html(frm) {
    let html = `
        <div class="pickup-tracking">
            <div class="row mb-3">
                <div class="col-md-12">
                    <h5>Pickup Progress for ${frm.doc.booking_number}</h5>
                    <div class="progress mb-3">
    `;
    
    let completed = frm.doc.guest_pickups.filter(p => p.pickup_status === 'Completed').length;
    let total = frm.doc.guest_pickups.length;
    let progress_percent = total > 0 ? (completed / total) * 100 : 0;
    
    html += `
                        <div class="progress-bar bg-success" style="width: ${progress_percent}%">
                            ${completed}/${total} Completed
                        </div>
                    </div>
                </div>
            </div>
    `;
    
    frm.doc.guest_pickups.forEach(function(pickup, index) {
        let status_class = get_status_class(pickup.pickup_status);
        let status_icon = get_status_icon(pickup.pickup_status);
        
        html += `
            <div class="pickup-item border rounded p-3 mb-2 ${status_class}">
                <div class="row">
                    <div class="col-md-1 text-center">
                        <h4>${pickup.pickup_order}</h4>
                    </div>
                    <div class="col-md-2">
                        <strong>${pickup.estimated_pickup_time}</strong>
                    </div>
                    <div class="col-md-3">
                        <strong>${pickup.guest_name}</strong><br>
                        <small>${pickup.pickup_location_name}</small>
                    </div>
                    <div class="col-md-3">
                        <small>${pickup.pickup_address}</small>
                    </div>
                    <div class="col-md-2">
                        <span class="badge ${status_class}">
                            ${status_icon} ${pickup.pickup_status}
                        </span>
                    </div>
                    <div class="col-md-1">
                        <button class="btn btn-sm btn-primary" onclick="update_pickup_status_inline('${pickup.pickup_order}')">
                            Update
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function get_status_class(status) {
    const classes = {
        'Pending': 'border-secondary',
        'Confirmed': 'border-info',
        'En Route': 'border-warning',
        'Arrived': 'border-warning',
        'Guest Located': 'border-success',
        'Completed': 'border-success bg-light',
        'No Show': 'border-danger'
    };
    return classes[status] || 'border-secondary';
}

function get_status_icon(status) {
    const icons = {
        'Pending': '⏳',
        'Confirmed': '✅',
        'En Route': '🚗',
        'Arrived': '📍',
        'Guest Located': '👤',
        'Completed': '✅',
        'No Show': '❌'
    };
    return icons[status] || '⏳';
}

// Mobile-friendly pickup status update
function update_pickup_status_inline(pickup_order) {
    let current_pickup = null;
    cur_frm.doc.guest_pickups.forEach(function(pickup) {
        if (pickup.pickup_order == pickup_order) {
            current_pickup = pickup;
        }
    });
    
    if (!current_pickup) return;
    
    let status_dialog = new frappe.ui.Dialog({
        title: __('Update Pickup Status'),
        fields: [
            {
                label: __('Guest'),
                fieldname: 'guest_name',
                fieldtype: 'Data',
                default: current_pickup.guest_name,
                read_only: 1
            },
            {
                label: __('Location'),
                fieldname: 'location',
                fieldtype: 'Data',
                default: current_pickup.pickup_location_name,
                read_only: 1
            },
            {
                label: __('Status'),
                fieldname: 'status',
                fieldtype: 'Select',
                options: 'Pending\nConfirmed\nEn Route\nArrived\nGuest Located\nCompleted\nNo Show',
                default: current_pickup.pickup_status,
                reqd: 1
            },
            {
                label: __('Notes'),
                fieldname: 'notes',
                fieldtype: 'Small Text',
                default: current_pickup.special_notes
            }
        ],
        primary_action_label: __('Update'),
        primary_action: function(values) {
            frappe.call({
                method: 'safari_excursion.utils.multiple_pickup_transport.update_pickup_status',
                args: {
                    excursion_booking: cur_frm.doc.name,
                    pickup_order: pickup_order,
                    status: values.status,
                    notes: values.notes
                },
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Status updated successfully'),
                            indicator: 'green'
                        });
                        cur_frm.reload_doc();
                        status_dialog.hide();
                    }
                }
            });
        }
    });
    
    status_dialog.show();
}

// Add pickup tracking button to custom buttons
function add_pickup_tracking_button(frm) {
    if (frm.doc.pickup_type === 'Individual Hotel Pickups' && frm.doc.guest_pickups && frm.doc.guest_pickups.length > 0) {
        frm.add_custom_button(__('Live Pickup Tracking'), function() {
            start_pickup_tracking(frm);
        }, __('Pickup Management'));
        
        frm.add_custom_button(__('Export Schedule'), function() {
            export_pickup_schedule(frm);
        }, __('Pickup Management'));
    }
}

// Enhance the show_pickup_management_buttons function
function show_pickup_management_buttons(frm) {
    // Add pickup schedule management buttons
    frm.add_custom_button(__('Create Pickup Schedule'), function() {
        create_pickup_schedule(frm);
    }, __('Pickup Management'));
    
    frm.add_custom_button(__('Send Pickup Confirmations'), function() {
        send_pickup_confirmations(frm);
    }, __('Pickup Management'));
    
    frm.add_custom_button(__('Driver Pickup Schedule'), function() {
        show_driver_pickup_schedule(frm);
    }, __('Pickup Management'));
    
    frm.add_custom_button(__('Optimize Route'), function() {
        optimize_pickup_route(frm);
    }, __('Pickup Management'));
    
    frm.add_custom_button(__('Send Pickup Reminders'), function() {
        send_pickup_reminders(frm);
    }, __('Pickup Management'));
    
    // Add new tracking and export buttons
    add_pickup_tracking_button(frm);
}