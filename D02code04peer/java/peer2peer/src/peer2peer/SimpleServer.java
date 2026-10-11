package peer2peer;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.ServerSocket;
import java.net.Socket;

public class SimpleServer implements Runnable {

	public void play() {
		BufferedReader in = null;
		ServerSocket listener = null;
		Socket socket = null;
		try {
			listener = new ServerSocket(5020);
			socket = listener.accept();
			if (socket != null) {
				System.out.println("Connected!");
			}
			in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
			
			while (true) {
				String inputMessage = in.readLine();
				if (inputMessage.equalsIgnoreCase("exit")) {
					break;
				}
				String outputMessage = "Peer: " + inputMessage;
				System.out.println(outputMessage);
			}
		}
		catch(IOException e) {
			e.printStackTrace();
		}
		finally {
			try {
				in.close();
				socket.close();
				listener.close();
				System.exit(0);
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}

	@Override
	public void run() {
		play();
	}
}
