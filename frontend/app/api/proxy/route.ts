// /app/api/proxy/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { Writable } from 'stream';

// Helper function to pipe stream
async function pipeStream(readable: ReadableStream<Uint8Array>, writable: Writable): Promise<void> {
    const reader = readable.getReader();
    return new Promise((resolve, reject) => {
        writable.on('finish', resolve);
        writable.on('error', reject);

        function pump() {
            reader.read().then(({ done, value }) => {
                if (done) {
                    writable.end();
                    return;
                }
                if (writable.write(value)) {
                    pump();
                } else {
                    writable.once('drain', pump);
                }
            }).catch(err => {
                writable.destroy(err);
                reject(err);
            });
        }
        pump();
    });
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const targetUrl = searchParams.get('target');

  if (!targetUrl) {
    return new NextResponse('Missing target URL parameter', { status: 400 });
  }

  try {
    console.log(`Proxy GET request to: ${targetUrl}`);
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Accept': request.headers.get('Accept') || 'application/json', // Prefer JSON for GET
      },
      // duplex not needed for non-streaming GET
    });

    // Check if the response was successful
    if (!response.ok) {
        // Attempt to read error details if available
        let errorBody = 'Backend request failed';
        try {
            errorBody = await response.text(); // Get text for logging
        } catch (e) { /* Ignore if body can't be read */ }
        console.error(`Proxy GET error: Backend responded with status ${response.status}`, errorBody);
        return new NextResponse(errorBody, { status: response.status, statusText: response.statusText });
    }

    // Since /available-models returns JSON, parse it directly
    // If other GET endpoints proxied here might not return JSON, add content-type check
    const data = await response.json();

    // Return the parsed JSON data
    // NextResponse.json handles setting Content-Type: application/json
    return NextResponse.json(data, {
        status: response.status,
        statusText: response.statusText,
        // We might not need to forward all headers if just returning JSON
        // headers: response.headers, // Consider which headers are needed
    });

  } catch (error: any) {
    console.error(`Proxy GET error to ${targetUrl}:`, error);
    // Check for specific fetch errors like connection refused
    if (error.cause?.code === 'ECONNREFUSED') {
        return new NextResponse(`Proxy error: Connection refused to backend at ${targetUrl}`, { status: 503 }); // Service Unavailable
    }
    return new NextResponse(`Proxy error: ${error.message}`, { status: 502 }); // Bad Gateway
  }
}

export async function POST(request: NextRequest) {
    const { searchParams } = new URL(request.url);
    const targetUrl = searchParams.get('target');

    if (!targetUrl) {
      return new NextResponse('Missing target URL parameter', { status: 400 });
    }

    try {
      console.log(`Proxy POST request to: ${targetUrl}`);

      // Copy headers, potentially filtering sensitive ones
      const headers = new Headers();
      request.headers.forEach((value, key) => {
        // Avoid forwarding Host, Content-Length (will be set automatically), etc.
        if (!['host', 'content-length'].includes(key.toLowerCase())) {
          headers.append(key, value);
        }
      });

      const backendResponse = await fetch(targetUrl, {
        method: 'POST',
        headers: headers,
        body: request.body, // Pass the readable stream directly
        // @ts-ignore - duplex is required for streaming fetch request body
        duplex: 'half'
      });

       // Handle the response from the backend (similar to GET)
      const readableStream = backendResponse.body;
      if (!readableStream) {
        return new NextResponse('Backend response stream is null.', { status: 500 });
      }

      const { readable, writable } = new TransformStream();
      pipeStream(readableStream, writable as unknown as Writable);

      return new NextResponse(readable, {
        status: backendResponse.status,
        statusText: backendResponse.statusText,
        headers: backendResponse.headers,
      });

    } catch (error: any) {
      console.error(`Proxy POST error to ${targetUrl}:`, error);
      return new NextResponse(`Proxy error: ${error.message}`, { status: 502 });
    }
  }

// You can add PUT, DELETE, etc. handlers similarly if needed
