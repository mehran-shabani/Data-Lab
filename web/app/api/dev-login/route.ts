import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

const AUTH_ACCESS_TTL_MIN = parseInt(process.env.AUTH_ACCESS_TTL_MIN || '60', 10)

interface DevLoginRequest {
  email: string
  org_name: string
}

interface DevLoginResponse {
  access_token: string
  token_type: string
  org_id: string
}

export async function POST(request: NextRequest) {
  try {
    const body: DevLoginRequest = await request.json()
    const { email, org_name } = body

    if (!email || !org_name) {
      return NextResponse.json(
        { error: 'Email and org_name are required' },
        { status: 400 }
      )
    }

    // Determine backend URL based on environment
    // In Docker: use container name, in local dev: use localhost
    const backendUrl = process.env.BACKEND_BASE_URL || 'http://localhost:8000'
    
    // Call backend dev login endpoint
    const backendResponse = await fetch(`${backendUrl}/auth/dev/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, org_name }),
    })

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}))
      return NextResponse.json(
        { error: errorData.detail || 'Backend authentication failed' },
        { status: backendResponse.status }
      )
    }

    const data: DevLoginResponse = await backendResponse.json()

    // Set HTTP-only cookie with the access token
    const cookieStore = await cookies()
    cookieStore.set('farda_token', data.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: AUTH_ACCESS_TTL_MIN * 60, // Convert minutes to seconds
      path: '/',
    })

    // Return success response
    return NextResponse.json({
      ok: true,
      org_id: data.org_id,
    })
  } catch (error) {
    console.error('Dev login error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
