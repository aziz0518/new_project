from datetime import timedelta
from django.utils.timezone import now
from django.db import connection
from django.db.models import (
    Count, Sum, F, Subquery, OuterRef, Window, Max, Min, Avg,
    Q, Exists, Case, When, Value, IntegerField, CharField, Prefetch
)
from django.db.models.functions import (
    Rank, RowNumber, TruncMonth, TruncDate
)
from rest_framework.views import APIView
from rest_framework.response import Response
from order.models import User, Order, Product, OrderProduct


class UserOrderSummaryView(APIView):
    def get(self, request):
        order_count = Count('order', distinct=True)
        total_spent = Sum(F('order__orderproduct__product__price') * F('order__orderproduct__quantity'))
        latest_order_subquery = Order.objects.filter(user=OuterRef('pk')).order_by('-ordered_at').values('ordered_at')[:1]

        last_orders = (
            Order.objects
            .annotate(row_number=Window(expression=RowNumber(), partition_by=[F('user')], order_by=F('ordered_at').desc()))
            .filter(row_number__lte=3)
            .values('id', 'user_id', 'ordered_at')
        )

        user_with_rank = (
            User.objects
            .annotate(order_count=order_count)
            .annotate(rank=Window(expression=Rank(), order_by=F('order_count').desc()))
            .values('id', 'username', 'order_count', 'rank')
        )

        users = (
            User.objects
            .annotate(
                total_orders=order_count,
                total_spent=total_spent,
                last_order_date=Subquery(latest_order_subquery)
            )
            .values('id', 'username', 'total_orders', 'total_spent', 'last_order_date')
        )

        user_orders = (
            Order.objects
            .select_related('user')
            .values('user__id', 'user__username', 'id', 'ordered_at')
            .order_by('user__id', '-ordered_at')
        )

        return Response({
            'user_summary': list(users),
            'user_ranks': list(user_with_rank),
            'last_3_orders': list(last_orders),
            'user_orders': list(user_orders),
        })


class OrderProductStatsView(APIView):
    def get(self, request):
        order_totals = (
            Order.objects
            .select_related('user')
            .annotate(
                total_price=Sum(F('orderproduct__product__price') * F('orderproduct__quantity'))
            )
            .values('id', 'user__username', 'total_price')
        )

        most_ordered_products = (
            Product.objects
            .annotate(
                total_quantity=Sum('orderproduct__quantity')
            )
            .order_by('-total_quantity')
            .values('id', 'name', 'total_quantity')[:5]
        )

        daily_orders = (
            Order.objects
            .annotate(order_date=TruncDate('ordered_at'))
            .values('order_date')
            .annotate(count=Count('id'))
            .order_by('order_date')
        )

        total_ordered_products = (
            OrderProduct.objects.aggregate(total=Sum('quantity'))
        )

        product_inventory_value = (
            Product.objects
            .annotate(total_value=F('price') * F('stock'))
            .values('id', 'name', 'price', 'stock', 'total_value')
        )

        order_price_range = (
            Order.objects
            .annotate(
                max_price=Max('orderproduct__product__price'),
                min_price=Min('orderproduct__product__price')
            )
            .values('id', 'user__username', 'max_price', 'min_price')
        )

        product_order_count = (
            Product.objects
            .annotate(order_count=Count('orderproduct__order', distinct=True))
            .values('id', 'name', 'order_count')
        )

        product_price_stats = Product.objects.aggregate(
            min_price=Min('price'),
            max_price=Max('price'),
            avg_price=Avg('price')
        )

        expensive_products_per_order = (
            OrderProduct.objects
            .select_related('order', 'product')
            .values('order_id', 'order__user__username')
            .annotate(
                max_price=Max('product__price')
            )
            .order_by('-max_price')
        )

        return Response({
            'order_totals': list(order_totals),
            'most_ordered_products': list(most_ordered_products),
            'daily_orders': list(daily_orders),
            'total_ordered_products': total_ordered_products,
            'product_inventory_value': list(product_inventory_value),
            'order_price_range': list(order_price_range),
            'product_order_count': list(product_order_count),
            'product_price_stats': product_price_stats,
            'expensive_products_per_order': list(expensive_products_per_order),
        })


class OrderAnalysisView(APIView):
    def get(self, request):
        shipped_count = Order.objects.filter(status="shipped").count()

        zero_stock_products = Product.objects.filter(stock=0).values('id', 'name')

        expensive_exists = Product.objects.annotate(
            expensive=Exists(
                Product.objects.filter(id=OuterRef('id'), price__gt=100)
            )
        ).filter(expensive=True).values('id', 'name', 'price')

        cheapest_product = Product.objects.order_by('price').first()
        orders_with_cheapest_product = Order.objects.filter(orderproduct__product=cheapest_product).values('id', 'user__username')

        product_stock_status = Product.objects.annotate(
            stock_status=Case(
                When(stock__gt=0, then=Value("In Stock")),
                default=Value("Out of Stock"),
                output_field=CharField()
            )
        ).values('id', 'name', 'stock', 'stock_status')

        multi_product_orders = Order.objects.annotate(
            product_count=Count('orderproduct')
        ).filter(product_count__gte=2).values('id', 'product_count')

        q_filtered_products = Product.objects.filter(
            Q(price__gt=100) | Q(stock__lt=10)
        ).values('id', 'name', 'price', 'stock')

        recent_orders = Order.objects.filter(ordered_at__gte=now() - timedelta(days=30)).values('id', 'ordered_at')

        
        order_totals = (
            OrderProduct.objects
            .values('order_id')
            .annotate(order_total=Sum(F('quantity') * F('product__price')))
        )

        orders_with_total_price = (
            Order.objects
            .annotate(
                total_price=Subquery(
                    order_totals.filter(order_id=OuterRef('id')).values('order_total')[:1]
                )
            )
            .values('id', 'total_price')
        )

        table_name = Product._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT AVG(price) FROM {table_name}")
            avg_price_result = cursor.fetchone()
            avg_price_rawsql = avg_price_result[0] if avg_price_result else None

        orders_with_products = Order.objects.prefetch_related(
            Prefetch('orderproduct_set', queryset=OrderProduct.objects.select_related('product'))
        )[:5]

        order_product_list = []
        for order in orders_with_products:
            items = []
            for item in order.orderproduct_set.all():
                items.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                })
            order_product_list.append({
                'order_id': order.id,
                'user': order.user.username,
                'products': items,
            })

        cheap_products = Product.objects.filter(price__lt=50).values('id', 'name')
        expensive_products = Product.objects.filter(price__gt=500).values('id', 'name')
        product_union = cheap_products.union(expensive_products)

        return Response({
            'shipped_count': shipped_count,
            'zero_stock_products': list(zero_stock_products),
            'expensive_exists': list(expensive_exists),
            'orders_with_cheapest_product': list(orders_with_cheapest_product),
            'product_stock_status': list(product_stock_status),
            'multi_product_orders': list(multi_product_orders),
            'q_filtered_products': list(q_filtered_products),
            'recent_orders': list(recent_orders),
            'cte_order_totals': list(orders_with_total_price),
            'avg_price_rawsql': avg_price_rawsql,
            'orders_with_prefetched_products': order_product_list,
            'product_union': list(product_union),
        })
