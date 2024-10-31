import tkinter as tk
from tkinter import messagebox, filedialog
import serial
from datetime import datetime
import glob

def list_serial_ports():
    return glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')

class SerialTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Terminal")
        self.serial_port = None

        # Configure the grid to make widgets expandable
        root.grid_rowconfigure(1, weight=1)  # Make receive_text expandable vertically
        root.grid_columnconfigure(0, weight=1)  # Make widgets expand horizontally

        # Toolbar frame
        self.toolbar = tk.Frame(root, bd=1, relief="raised")
        self.toolbar.grid(row=0, column=0, sticky="we", padx=5, pady=5)

        # Port selection
        self.port_label = tk.Label(self.toolbar, text="Port:")
        self.port_label.pack(side="left", padx=5, pady=5)

        self.port_var = tk.StringVar()
        self.port_dropdown = tk.OptionMenu(self.toolbar, self.port_var, [])
        self.port_dropdown.pack(side="left", padx=5, pady=5)

        self.refresh_button = tk.Button(self.toolbar, text="Refresh Ports", command=self.refresh_ports)
        self.refresh_button.pack(side="left", padx=5, pady=5)

        # Baud rate entry
        self.baudrate_label = tk.Label(self.toolbar, text="Baudrate:")
        self.baudrate_label.pack(side="left", padx=5, pady=5)

        self.baudrate_entry = tk.Entry(self.toolbar, width=10)
        self.baudrate_entry.insert(0, "9600")
        self.baudrate_entry.pack(side="left", padx=5, pady=5)

        # Connect button
        self.connect_button = tk.Button(self.toolbar, text="Connect", command=self.connect_serial)
        self.connect_button.pack(side="left", padx=5, pady=5)

        # Checkbox for showing datetime
        self.show_timestamp = tk.BooleanVar(value=False)
        self.timestamp_checkbox = tk.Checkbutton(self.toolbar, text="Show Datetime", variable=self.show_timestamp)
        self.timestamp_checkbox.pack(side="left", padx=5, pady=5)

        # Clear button to clear received messages
        self.clear_button = tk.Button(self.toolbar, text="Clear", command=self.clear_received_text)
        self.clear_button.pack(side="left", padx=5, pady=5)

        # Export button to save received messages
        self.export_button = tk.Button(self.toolbar, text="Export", command=self.export_log)
        self.export_button.pack(side="left", padx=5, pady=5)

        # Frame for receive_text and scrollbar
        self.text_frame = tk.Frame(root)
        self.text_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # Text box for displaying received messages
        self.receive_text = tk.Text(self.text_frame, height=10, width=50, state="disabled", wrap="word")
        self.receive_text.pack(side="left", fill="both", expand=True)

        # Scrollbar for the text box
        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.receive_text.yview)
        self.scrollbar.pack(side="right", fill="y")

        # Link the scrollbar to the text widget
        self.receive_text.config(yscrollcommand=self.scrollbar.set)

        # Context menu for receive_text
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_selected_text)

        # Bind right-click event to show the context menu
        self.receive_text.bind("<Button-3>", self.show_context_menu)

        # Text entry and button for sending messages
        self.send_entry = tk.Entry(root, width=30)
        self.send_entry.grid(row=2, column=0, padx=5, pady=5, sticky="we")

        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.grid(row=2, column=0, padx=5, pady=5, sticky="e")

        self.refresh_ports()

    def refresh_ports(self):
        ports = list_serial_ports()
        self.port_var.set('')
        menu = self.port_dropdown["menu"]
        menu.delete(0, "end")
        for port in ports:
            menu.add_command(label=port, command=lambda p=port: self.port_var.set(p))

    def connect_serial(self):
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_serial()
            return

        port = self.port_var.get()
        baudrate = self.baudrate_entry.get()

        if not port:
            messagebox.showerror("Error", "Please select a port.")
            return

        try:
            self.serial_port = serial.Serial(port, baudrate=int(baudrate), timeout=1)
            self.connect_button.config(text="Disconnect")
            self.root.after(100, self.receive_message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to port: {e}")

    def disconnect_serial(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
        self.connect_button.config(text="Connect")

    def receive_message(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                message = self.serial_port.readline().decode("utf-8").strip()
                if message:
                    # Check if the timestamp should be shown
                    if self.show_timestamp.get():
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        formatted_message = f"{timestamp} - {message}"
                    else:
                        formatted_message = message

                    # Display the message in the text box
                    self.receive_text.config(state="normal")
                    self.receive_text.insert("end", formatted_message + "\n")
                    self.receive_text.config(state="disabled")
                    self.receive_text.see("end")
            except Exception as e:
                messagebox.showerror("Error", f"Error receiving message: {e}")
                self.disconnect_serial()
                return
            self.root.after(100, self.receive_message)

    def send_message(self):
        if self.serial_port and self.serial_port.is_open:
            message = self.send_entry.get()
            try:
                self.serial_port.write(message.encode("utf-8"))
                self.send_entry.delete(0, "end")
            except Exception as e:
                messagebox.showerror("Error", f"Error sending message: {e}")

    def clear_received_text(self):
        """Clear the received text box."""
        self.receive_text.config(state="normal")
        self.receive_text.delete(1.0, "end")
        self.receive_text.config(state="disabled")

    def show_context_menu(self, event):
        """Show the context menu on right-click."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selected_text(self):
        """Copy the selected text from the receive_text box to the clipboard."""
        try:
            selected_text = self.receive_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            messagebox.showinfo("Copy", "No text selected to copy.")

    def export_log(self):
        """Export all received text content as a .log file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Log files", "*.log"), ("All files", "*.*")])
        if file_path:
            try:
                content = self.receive_text.get(1.0, "end-1c")  # Get all text from the text box
                with open(file_path, "w") as log_file:
                    log_file.write(content)
                messagebox.showinfo("Export Log", f"Log saved successfully as {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {e}")


# Create main window
root = tk.Tk()
app = SerialTerminal(root)
root.mainloop()
