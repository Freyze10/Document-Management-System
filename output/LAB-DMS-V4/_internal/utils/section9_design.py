STYLESHEET = """
QGroupBox#section9Group {
    font-size: 14px;
    font-weight: 600;
    color: #212529;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 2.0ex;
    background-color: #ffffff;
    padding: 8px 10px;
}

QGroupBox#section9Group::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    left: 15px;
    margin-left: 0px;
    color: #34495e;
}

QLineEdit#propertyName {
    font-size: 12px;
    font-weight: bold;
    padding: 4px 8px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: #ffffff;
    min-width: 150px;
    max-width: 200px; /* Fixed width for property names */
    min-height: 26px;
    selection-background-color: #aed6f1;
    color: #343a40;
}

QLineEdit#propertyName:focus {
    border: 1px solid #007bff;
    background-color: #e9f5ff;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25);
}

QLineEdit#propertyName.empty_field {
    border: 1px solid #dc3545;
    background-color: #ffebeb;
}

QLineEdit#propertyName.empty_field:focus {
    border: 1px solid #dc3545;
    box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.25);
}

QPushButton#actionButton {
    background-color: #6c757d; /* Neutral gray for action buttons */
    color: #ffffff;
    font-size: 12px;
    font-weight: 500;
    padding: 5px 8px;
    border: none;
    border-radius: 4px;
    min-width: 26px;
    max-width: 26px; /* Small buttons for up/down/delete */
    min-height: 26px;
    
}
QPushButton#actionButton_delete {
    background-color: #dc3545; /* Neutral gray for action buttons */
    color: #ffffff;
    font-size: 12px;
    font-weight: 500;
    padding: 5px 8px;
    border: none;
    border-radius: 4px;
    min-width: 40px;
    max-width: 80px; /* Small buttons for up/down/delete */
    min-height: 26px;
}
QPushButton#actionButton_delete:hover {
    background-color: #bb2d3b;  
}

QPushButton#actionButton_delete:pressed {
    background-color: #a52834;   
}
QPushButton#actionButton:hover {
    background-color: #5a6268;
}

QPushButton#actionButton:pressed {
    background-color: #495057;
}

QPushButton#actionButton:disabled {
    background-color: #d3d3d3;
    color: #6c757d;
}

QPushButton#addPropertyButton {
    background-color: #28a745; /* Green for add button */
    color: #ffffff;
    font-size: 14px;
    font-weight: 600;
    padding: 4px 14px;
    border: none;
    border-radius: 6px;
    min-width: 100px;
    min-height: 30px;
}

QPushButton#addPropertyButton:hover {
    background-color: #218838;
}

QPushButton#addPropertyButton:pressed {
    background-color: #1e7e34;
}

QLabel#propertyLabel {
    font-size: 14px;
    font-weight: 500;
    color: #495057;
    padding-bottom: 2px;
    background-color: transparent;
}
"""