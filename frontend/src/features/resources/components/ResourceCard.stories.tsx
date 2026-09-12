import type { Meta, StoryObj } from '@storybook/react'
import { ResourceCard } from './ResourceCard'

const meta: Meta<typeof ResourceCard> = {
  title: 'Resources/ResourceCard',
  component: ResourceCard,
  tags: ['autodocs'],
}
export default meta

type Story = StoryObj<typeof ResourceCard>

export const ActiveTeamResource: Story = {
  args: {
    resource: {
      public_id: 'resource-item-id',
      name: 'OpenAI API key',
      type: 'api_key',
      target: 'team',
      metadata: { provider: 'OpenAI', environment: 'sandbox' },
      is_revoked: false,
      hackathon: { public_id: 'hackathon-id', name: 'HackYeah' },
    },
  },
}

export const RevokedIndividualResource: Story = {
  args: {
    resource: {
      public_id: 'revoked-resource-item-id',
      name: 'Anthropic API key',
      type: 'api_key',
      target: 'individual',
      metadata: { provider: 'Anthropic' },
      is_revoked: true,
      hackathon: { public_id: 'hackathon-id', name: 'HackYeah' },
    },
  },
}
