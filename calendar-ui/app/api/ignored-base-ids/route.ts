import { NextRequest, NextResponse } from 'next/server'
import { execSync } from 'child_process'
import path from 'path'

export async function GET() {
  try {
    const scriptPath = path.resolve(process.cwd(), '../manage_ignored_base_ids.py')
    const command = `python3 "${scriptPath}" list`
    
    const output = execSync(command, { encoding: 'utf-8', cwd: process.cwd() })
    const ignored = JSON.parse(output)
    
    return NextResponse.json(ignored)
  } catch (error: any) {
    console.error('Error fetching ignored base IDs:', error)
    return NextResponse.json(
      { error: 'Failed to fetch ignored base IDs', details: error.message },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { base_id, subject, reason } = body
    
    const scriptPath = path.resolve(process.cwd(), '../manage_ignored_base_ids.py')
    const command = `python3 "${scriptPath}" add "${base_id}" "${subject || ''}" "${reason || 'User ignored'}"`
    
    execSync(command, { encoding: 'utf-8', cwd: process.cwd() })
    
    return NextResponse.json({ success: true })
  } catch (error: any) {
    console.error('Error adding ignored base ID:', error)
    return NextResponse.json(
      { error: 'Failed to add ignored base ID', details: error.message },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const base_id = searchParams.get('base_id')
    
    if (!base_id) {
      return NextResponse.json(
        { error: 'base_id is required' },
        { status: 400 }
      )
    }
    
    const scriptPath = path.resolve(process.cwd(), '../manage_ignored_base_ids.py')
    const command = `python3 "${scriptPath}" remove "${base_id}"`
    
    execSync(command, { encoding: 'utf-8', cwd: process.cwd() })
    
    return NextResponse.json({ success: true })
  } catch (error: any) {
    console.error('Error removing ignored base ID:', error)
    return NextResponse.json(
      { error: 'Failed to remove ignored base ID', details: error.message },
      { status: 500 }
    )
  }
}

