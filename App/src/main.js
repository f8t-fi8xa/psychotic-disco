const {app, BrowserWindow, Menu} = require("electron");

const createMainWindow = () => {
    const mainWindow = new BrowserWindow({
    });

    mainWindow.maximize()
    mainWindow.loadFile("../resources/inventory.html")
}

app.whenReady().then(() => {
    createMainWindow()

    const menu = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'Quit',
                    click: () => end(),
                    accelerator: 'Ctrl+q'
                },
                {
                    label: 'Open Dev Tools',
                    click: () => {
                        let webContents = BrowserWindow.getFocusedWindow().webContents;
                        if (webContents.isDevToolsOpened()) webContents.closeDevTools();
                        else webContents.openDevTools();
                    },
                    accelerator: 'F12'
                }
            ]
        }
    ]
    const mainMenu = Menu.buildFromTemplate(menu);
    Menu.setApplicationMenu(mainMenu);

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createMainWindow()
            })
})

function end() {
    app.quit();
}

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') end()
})