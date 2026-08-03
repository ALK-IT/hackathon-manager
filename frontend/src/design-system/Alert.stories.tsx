import type { Meta, StoryObj } from '@storybook/react'
import { Alert } from './Alert'

const meta: Meta<typeof Alert> = {
  title: 'Design System/Alert',
  component: Alert,
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['error', 'info'] },
  },
}
export default meta

type Story = StoryObj<typeof Alert>

export const Error: Story = {
  args: {
    children: 'Failed to load hackathons. Please try again.',
    variant: 'error',
  },
}

export const Info: Story = {
  args: {
    children: 'There are no hackathons to display.',
    variant: 'info',
  },
}
