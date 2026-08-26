import type { Meta, StoryObj } from '@storybook/react'
import { Countdown } from './Countdown'

const meta: Meta<typeof Countdown> = {
  title: 'Design System/Countdown',
  component: Countdown,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof Countdown>

export const BeforeStart: Story = {
  args: {
    startDate: '2099-09-01T10:00:00Z',
    endDate: '2099-09-02T18:00:00Z',
  },
}

export const Completed: Story = {
  args: {
    startDate: '2020-09-01T10:00:00Z',
    endDate: '2020-09-02T18:00:00Z',
  },
}
