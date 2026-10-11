package peer2peer;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.net.Socket;
import java.util.Scanner;

public class SimpleClient implements Runnable {
	
	public void play() {
		BufferedWriter out = null;
		Socket socket = null;
		Scanner scanner = new Scanner(System.in);
		try {
			socket = new Socket("localhost", 5021);
			out = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream()));
			while(true) {
				String outputMessage = scanner.nextLine();
				out.write(outputMessage + "\n");
				out.flush();
				if (outputMessage.equalsIgnoreCase("exit")) {
					break;
				}
			}
		}
		catch(IOException e) {
			e.printStackTrace();
		}
		finally {
				try {
					scanner.close();
					if (socket != null)
					socket.close();
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
