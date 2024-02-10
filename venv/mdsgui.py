import tkinter as tk
from tkinter import ttk
# datafile.py
import datafile

def build_tree(tree, parent, node):
    item = tree.insert(parent, 'end', text=f"{node['ddcnum']} - {node['word']}")
    if node.get('children'):
        for key, child_node in node['children'].items():
            build_tree(tree, item, child_node)

def search_tree(tree, query, results_listbox, parent='', visited=None):
    if visited is None:
        visited = set()

    items = tree.get_children(parent)
    matching_items = []

    for item in items:
        text = tree.item(item, 'text')
        if query.lower() in text.lower() and item not in visited:
            matching_items.append(text)
            results_listbox.insert(tk.END, text)
            visited.add(item)

        matching_items += search_tree(tree, query, results_listbox, item, visited)

    return matching_items

def on_search_entry_change(entry, tree, results_listbox):
    query = entry.get()
    results_listbox.delete(0, tk.END)  # Clear the listbox

    if query:
        search_tree(tree, query, results_listbox)

def collapse_all(tree):
    items = tree.get_children()
    for item in items:
        tree.item(item, open=False)
        #collapse_all(tree)
        

def main():
    # Get Data
    data = datafile.tree

    # Create main window
    root = tk.Tk()
    root.title("MDS Lookup")
    root.geometry("800x600")  # Set the dimensions of the main window

    # Create a label for the search box
    search_label = tk.Label(root, text="Search:")
    search_label.pack(pady=5)

    # Create a search entry
    search_entry = tk.Entry(root, width=30)
    search_entry.pack(pady=10)
    search_entry.bind('<KeyRelease>', lambda event: on_search_entry_change(search_entry, tree, results_listbox))

    # Create a listbox for search results
    results_listbox = tk.Listbox(root, selectmode=tk.SINGLE, width=50, height=5)
    results_listbox.pack(pady=10)

    # Create a "Collapse All" button
    collapse_button = tk.Button(root, text="Collapse All", command=lambda: collapse_all(tree))
    collapse_button.pack()

    # Create a treeview widget with vertical lines and boxes
    style = ttk.Style()
    style.configure("Treeview", font=('Helvetica', 10), rowheight=25)
    style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))

    tree = ttk.Treeview(
        root,
        style="Treeview",
        columns=('col1',),  # No additional columns
        displaycolumns=('col1',),  # Only show the first column
        height=20,
        selectmode='extended'
    )

    tree.column('#0', width=800, anchor='w')

    tree.heading('#0', text='Tree View', anchor='w')

    tree.pack(expand=True, fill=tk.BOTH)

    # Build the tree
    build_tree(tree, '', data['root'])

    # Collapse all nodes initially
    collapse_all(tree)

    # Run the main loop
    root.mainloop()

if __name__ == "__main__":
    main()
