from datetime import datetime, time, timedelta

def get_shift_name_and_start(check_time, delta_hr):
    # Define shifts
    shifts = {
        'Morning': time(8, 0),     # 8AM to 6PM
        'Afternoon': time(14, 0),  # 2PM to 12AM
        'Evening': time(22, 0),    # 9PM to 7AM (next day)
    }

    for name, start_t in shifts.items():
        start_dt = datetime.combine(check_time.date(), start_t)

        # Adjust Evening shift if early morning
        if name == 'Evening':
            if check_time.time() < time(8, 0):  # 12AM–7:59AM belongs to previous evening
                start_dt -= timedelta(days=1)

        end_dt = start_dt + timedelta(hours=delta_hr)

        if start_dt <= check_time < end_dt:
            return name, start_dt

    return None, None  # fallback if no match

# Simulate every hour from 12:00 AM to 11:00 PM
delta_hr = 10
base_date = datetime(2025, 5, 19)

print("Time       | Shift     | Start Time")
print("----------------------------------------")

for hour in range(24):
    current_time = datetime.combine(base_date, time(hour, 0))
    shift_name, start_time = get_shift_name_and_start(current_time, delta_hr)

    shift_str = shift_name if shift_name else "Unknown"
    start_str = start_time.strftime('%Y-%m-%d %I:%M %p') if start_time else "N/A"

    print(f"{current_time.strftime('%I:%M %p')} | {shift_str:<10} | {start_str}")
