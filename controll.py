import paramiko
import threading
import sys
import os
import json


def send_input(channel):
    try:
        while True:
            user_input = sys.stdin.readline()
            channel.send(user_input)
    except EOFError:
        pass


def run_remote_script(config):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=config["server_ip"],
            username=config["username"],
            key_filename=config["key_path"],
        )
        command = f"cd {config['script_path']} && bash {config['script']}"
        channel = client.get_transport().open_session()
        channel.get_pty()
        channel.exec_command(command)

        input_thread = threading.Thread(target=send_input, args=(channel,))
        input_thread.daemon = True
        input_thread.start()

        while True:
            if channel.recv_ready():
                output = channel.recv(1024).decode()
                if "clear" in output:
                    os.system("cls" if os.name == "nt" else "clear")
                else:
                    sys.stdout.write(output)
                    sys.stdout.flush()

            if channel.recv_stderr_ready():
                error_output = channel.recv_stderr(1024).decode()
                sys.stderr.write(error_output)
                sys.stderr.flush()

            if channel.exit_status_ready():
                break

        print("Завершение работы скрипта.")
        client.close()

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
        run_remote_script(config)
    except FileNotFoundError:
        print("Файл config.json не найден.")
    except json.JSONDecodeError:
        print("Ошибка в формате файла config.json.")
