/**
 * Dashboard Assignments Page
 */
import AssignmentList from '@/components/AssignmentList';

export const metadata = {
  title: 'Assignments - Cyloid',
  description: 'Manage workflow assignments',
};

export default function AssignmentsPage() {
  return <AssignmentList />;
}
