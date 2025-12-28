
    async function resolverTicket(ticketId) {
        if (!confirm('¿Marcar este ticket como resuelto?')) return;

        try {
            const response = await fetch(`/api/tickets/${ticketId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    estado: 'resuelto'
                })
            });

            const data = await response.json();

            if (data.success) {
                alert('✅ Ticket marcado como resuelto');
                location.reload();
            } else {
                alert('❌ Error al actualizar el ticket');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('❌ Error de conexión');
        }
    }

    function verDetalle(ticketId) {
        // Aquí podrías abrir un modal con más detalles
        alert(`Funcionalidad de detalle del ticket #${ticketId} - Por implementar`);
    }

    // Auto-refresh cada 30 segundos
    setTimeout(() => {
        location.reload();
    }, 30000);