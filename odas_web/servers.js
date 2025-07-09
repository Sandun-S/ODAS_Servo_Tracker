// Load modules
const StringDecoder = require('string_decoder').StringDecoder;
const net = require('net');
const dgram = require('dgram');
const udpClient = dgram.createSocket('udp4');

let trackingServer;
let potentialServer;

// === TCP Server for Tracking Sources ===
let remainingTrack = '';

exports.startTrackingServer = (odasStudio) => {
  trackingServer = net.createServer();
  trackingServer.on('connection', handleConnection);
  trackingServer.listen(9000, () => {
    console.log('Tracking server listening on', trackingServer.address());
  });

  function handleConnection(conn) {
    const remoteAddress = conn.remoteAddress + ':' + conn.remotePort;
    console.log('New tracking client from', remoteAddress);

    conn.on('data', onConnData);
    conn.once('close', onConnClose);
    conn.on('error', onConnError);

    function onConnData(d) {
      const decoder = new StringDecoder();
      const stream = remainingTrack + decoder.write(d);
      const strs = stream.split("}\n{");

      if (strs.length < 2) {
        remainingTrack = stream;
        return;
      }

      strs.forEach((str, index) => {
        if (index === strs.length - 1) {
          remainingTrack = str;
          return;
        }

        if (str.charAt(0) !== '{') str = '{' + str;
        if (str.charAt(str.length - 2) !== '}') {
          if (str.charAt(str.length - 3) !== '}') str += '}';
        }

        try {
          if (
            odasStudio &&
            odasStudio.mainWindow &&
            odasStudio.mainWindow.webContents
          ) {
            odasStudio.mainWindow.webContents.send('newTracking', str);
          }
        } catch (err) {
          console.warn('[Tracking] GUI send error:', err.message);
        }

        const msgBuffer = Buffer.from(str);
        udpClient.send(msgBuffer, 9900, '127.0.0.1', (err) => {
          if (err) console.error('UDP send error (9900):', err);
        });

        if (
          odasStudio &&
          odasStudio.odas &&
          typeof odasStudio.odas.odas_process === 'undefined'
        ) {
          try {
            if (
              odasStudio.mainWindow &&
              odasStudio.mainWindow.webContents
            ) {
              odasStudio.mainWindow.webContents.send('remote-online');
            }
          } catch (_) {}
        }
      });
    }

    function onConnClose() {
      console.log('Tracking connection from', remoteAddress, 'closed');
      if (
        odasStudio &&
        odasStudio.mainWindow &&
        odasStudio.mainWindow.webContents
      ) {
        odasStudio.mainWindow.webContents.send('remote-offline');
      }
    }

    function onConnError(err) {
      console.log('Tracking connection error from', remoteAddress, ':', err.message);
    }
  }
};

// === TCP Server for Potential Sources ===
let remainingPot = '';

exports.startPotentialServer = (odasStudio) => {
  potentialServer = net.createServer();
  potentialServer.on('connection', handlePotConnection);
  potentialServer.listen(9001, () => {
    console.log('Potential server listening on', potentialServer.address());
  });

  function handlePotConnection(conn) {
    const remoteAddress = conn.remoteAddress + ':' + conn.remotePort;
    console.log('New potential client from', remoteAddress);

    conn.on('data', onConnData);
    conn.once('close', onConnClose);
    conn.on('error', onConnError);

    function onConnData(d) {
      const decoder = new StringDecoder();
      const stream = remainingPot + decoder.write(d);
      const strs = stream.split("}\n{");

      if (strs.length < 2) {
        remainingPot = stream;
        return;
      }

      strs.forEach((str, index) => {
        if (index === strs.length - 1) {
          remainingPot = str;
          return;
        }

        if (str.charAt(0) !== '{') str = '{' + str;
        if (str.charAt(str.length - 2) !== '}') {
          if (str.charAt(str.length - 3) !== '}') str += '}';
        }

        try {
          if (
            odasStudio &&
            odasStudio.mainWindow &&
            odasStudio.mainWindow.webContents
          ) {
            odasStudio.mainWindow.webContents.send('newPotential', str);
          }
        } catch (err) {
          console.warn('[Potential] GUI send error:', err.message);
        }

        const msgBuffer = Buffer.from(str);
        udpClient.send(msgBuffer, 9901, '127.0.0.1', (err) => {
          if (err) console.error('UDP send error (9901):', err);
        });

        if (
          odasStudio &&
          odasStudio.odas &&
          typeof odasStudio.odas.odas_process === 'undefined'
        ) {
          try {
            if (
              odasStudio.mainWindow &&
              odasStudio.mainWindow.webContents
            ) {
              odasStudio.mainWindow.webContents.send('remote-online');
            }
          } catch (_) {}
        }
      });
    }

    function onConnClose() {
      console.log('Potential connection from', remoteAddress, 'closed');
      if (
        odasStudio &&
        odasStudio.mainWindow &&
        odasStudio.mainWindow.webContents
      ) {
        odasStudio.mainWindow.webContents.send('remote-offline');
      }
    }

    function onConnError(err) {
      console.log('Potential connection error from', remoteAddress, ':', err.message);
    }
  }
};
