import paramiko
import os
import schedule
import time
import random

# Fungsi untuk ping ke IP
def ping_ip(ip):
    response = os.system(f"ping -c 1 {ip}")
    return response == 0

# Fungsi untuk mengirim perintah konfigurasi ke MikroTik via SSH
def send_config_to_mikrotik(ip, username, password, config_commands):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, username=username, password=password)
        for command in config_commands:
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            if output:
                print(f"Output dari {ip}: {output}")
            if error:
                print(f"Error dari {ip}: {error}")
        ssh.close()
        return True
    except Exception as e:
        print(f"Gagal menghubungi {ip}: {str(e)}")
        return False

# Fungsi untuk mengubah frekuensi
def configure_frequency(ip, frequencies):
    frequency = frequencies.get(ip, None)
    if frequency:
        return [f"/interface wireless set wlan-room frequency={frequency}"]
    else:
        print(f"Frekuensi untuk IP {ip} tidak ditemukan.")
        return []

# Fungsi untuk reboot
def configure_reboot(ip, frequencies):
    return ["/system reboot"]
    
# Fungsi untuk menghasilkan frekuensi acak
def generate_random_frequencies(ip_list, num_frequencies=1):
    channel_to_frequency = [2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452, 2457, 2462, 2467, 2472]
    frequencies = {}
    
    for ip in ip_list:
        random_frequencies = random.sample(channel_to_frequency, num_frequencies)
        frequencies[ip] = random_frequencies[0]  # Ambil satu frekuensi acak
    return frequencies

# Fungsi untuk looping frekuensi
def loop_frequencies(ip_list, file_path):
    channel_to_frequency = [
        2412, 2417, 2422, 2427, 2432,
        2437, 2442, 2447, 2452, 2457,
        2462, 2467, 2472
    ]

    total_frequencies = len(channel_to_frequency)
    frequencies = {}

    for index, ip in enumerate(ip_list):
        frequency = channel_to_frequency[index % total_frequencies]
        frequencies[ip] = frequency

    with open(file_path, "w") as freq_file:
        for ip, frequency in frequencies.items():
            freq_file.write(f"{ip}:{frequency}\n")
    print(f"Frekuensi looping berhasil disimpan di {file_path}.")
    return frequencies

# Fungsi untuk looping frekuensi 1, 6, 11
def loop_frequencies_with_1_6_11(ip_list, file_path="frequencies.txt"):
    channel_to_frequency = [2412, 2437, 2462]
    frequencies = {}

    for index, ip in enumerate(ip_list):
        frequency = channel_to_frequency[index % len(channel_to_frequency)]
        frequencies[ip] = frequency

    with open(file_path, "w") as freq_file:
        for ip, frequency in frequencies.items():
            freq_file.write(f"{ip}:{frequency}\n")
    
    print(f"Frekuensi 1, 6, 11 telah disimpan ke {file_path}.")
    return frequencies

# Baca file IP
def load_ips(file_path):
    with open(file_path, "r") as ip_file:
        return [line.strip() for line in ip_file.readlines()]

# Baca file password
def load_passwords(file_path):
    passwords = {}
    with open(file_path, "r") as password_file:
        for line in password_file:
            if not line.strip():
                continue
            parts = line.strip().split(":")
            if len(parts) == 2:
                ip, password = parts
                passwords[ip] = password
            else:
                print(f"Format baris salah: {line.strip()}")
    return passwords

# Baca file frekuensi
def load_frequencies(file_path):
    frequencies = {}
    with open(file_path, "r") as freq_file:
        for line in freq_file:
            parts = line.strip().split(":")
            if len(parts) == 2:
                ip, freq = parts
                frequencies[ip] = freq
    return frequencies

# Fungsi untuk menjalankan konfigurasi untuk IP
def execute_ip_config(ip, config_commands):
    if ping_ip(ip):
        print(f"Ping ke {ip} berhasil!")
        password = passwords.get(ip, None)
        if password:
            if send_config_to_mikrotik(ip, "admin", password, config_commands):
                print(f"Konfigurasi berhasil diterapkan ke IP {ip}")
            else:
                print(f"Gagal mengirim konfigurasi ke IP {ip}")
        else:
            print(f"Tidak ada password untuk IP {ip}!")
    else:
        print(f"Ping ke {ip} gagal! IP tidak dapat dijangkau.")



# Fungsi untuk menjadwalkan konfigurasi untuk IP tertentu
def schedule_for_ips(ip_list, time_str, config_function, frequencies):
    for ip in ip_list:
        config_commands = config_function(ip, frequencies)
        schedule.every().day.at(time_str).do(execute_ip_config, ip, config_commands)
        print(f"Tugas telah dijadwalkan untuk {ip} pada {time_str}.")
        time.sleep(1)

# Fungsi untuk eksekusi segera
def execute_now(ip_list, config_function, frequencies):
    for ip in ip_list:
        if ping_ip(ip):
            config_commands = config_function(ip, frequencies)
            execute_ip_config(ip, config_commands)
        else:
            print(f"IP {ip} tidak merespons. Konfigurasi tidak diterapkan.")

# Fungsi untuk meminta input valid
def get_valid_input(prompt, valid_options):
    while True:
        choice = input(prompt)
        if choice in valid_options:
            return choice
        else:
            print(f"Pilihan tidak valid. Silakan pilih dari {valid_options}.")

# Load data dari file
ip_addresses = load_ips("ip.txt")
passwords = load_passwords("passwords.txt")
frequencies = load_frequencies("frequencies.txt")  # Load frequencies at the beginning

def handle_frequency_config():
    global frequencies
    ip_choice = get_valid_input("Pilih: (1) Semua IP, (2) Satu IP, (3) Loop Frekuensi, (4) Generate Frekuensi Acak, (5) Loop Frekuensi 1,6,11, (6) Keluar: ", ["1", "2", "3", "4", "5", "6"])
    
    if ip_choice == "1":
        time_str = input("Masukkan waktu (format HH:MM, 24 jam) untuk menjadwalkan konfigurasi: ")
        frequencies = loop_frequencies(ip_addresses, "frequencies.txt")  # Muat frekuensi yang baru
        schedule_for_ips(ip_addresses, time_str, configure_frequency, frequencies)
    
    elif ip_choice == "2":
        while True:
            single_ip = input("Masukkan IP yang akan dikonfigurasi: ")
            if single_ip in ip_addresses:
                execute_now([single_ip], configure_frequency, frequencies)
                break
            else:
                print(f"IP {single_ip} tidak ditemukan dalam daftar.")
    
    elif ip_choice == "3":
        while True:
            frequencies = loop_frequencies(ip_addresses, "frequencies.txt")
            time.sleep(5)  # Tunggu beberapa detik sebelum looping lagi
            
            continue_choice = get_valid_input("Ingin melanjutkan looping frekuensi? (y/n): ", ["y", "n"])
            if continue_choice == "n":
                break
    
    elif ip_choice == "4":
        frequencies = generate_random_frequencies(ip_addresses)
        with open("frequencies.txt", "w") as freq_file:
            for ip, freq in frequencies.items():
                freq_file.write(f"{ip}:{freq}\n")
        print("Frekuensi acak berhasil disimpan.")
    
    elif ip_choice == "5":
        frequencies = loop_frequencies_with_1_6_11(ip_addresses, "frequencies.txt")
    
    elif ip_choice == "6":
        return False
    
    else:
        print("Pilihan tidak valid.")
    
    return True

def handle_reboot_config():
    ip_choice = get_valid_input("Pilih: (1) Semua IP, (2) Satu IP, (3) Keluar: ", ["1", "2", "3"])
    
    if ip_choice == "1":
        time_str = input("Masukkan waktu (format HH:MM, 24 jam) untuk menjadwalkan konfigurasi: ")
        schedule_for_ips(ip_addresses, time_str, configure_reboot, {})
    
    elif ip_choice == "2":
        while True:
            single_ip = input("Masukkan IP yang akan dikonfigurasi: ")
            if single_ip in ip_addresses:
                execute_now([single_ip], configure_reboot, {})
                break
            else:
                print(f"IP {single_ip} tidak ditemukan dalam daftar.")
    
    elif ip_choice == "3":
        return False
    
    else:
        print("Pilihan tidak valid.")
    
    return True

def main():
    while True:
        try:
            config_type = get_valid_input("Pilih konfigurasi: (1) Ubah Frekuensi, (2) Reboot, (3) Keluar: ", ["1", "2", "3"])

            if config_type == "1":
                while handle_frequency_config():
                    pass
            elif config_type == "2":
                while handle_reboot_config():
                    pass
            elif config_type == "3":
                print("Keluar dari program.")
                break
            
            while True:
                schedule.run_pending()
                time.sleep(1)
                if not schedule.get_jobs():
                    break
        except KeyboardInterrupt:
            print("\nProgram dihentikan.")
            break

# Jalankan fungsi utama
if __name__ == "__main__":
    main()
