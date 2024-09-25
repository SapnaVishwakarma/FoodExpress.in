import re
from django.shortcuts import redirect, render
from django.core.mail import send_mail, BadHeaderError
from User.views import deco_auth
from .models import Food, Items, Order
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages


def Home(request):
    if request.method == "POST":
        message=request.POST.get('message')
        mail=request.POST.get('mail')
        name=request.POST.get('name')
        address=request.POST.get('address')
        subject= str(name)+' wants to contact with ChalkBoard Art'
        try:
            send_mail(subject,'name '+str(name) +'\n' +'\n'+'email ' + str(mail) +'\n'+'address ' + str(address)+'\n'+'message ' + str(message),mail,['chalkboardarttd@gmail.com'])
            messages.success(request,'Message Successfully Send')
        except BadHeaderError:
            print("Invalid subject")
            messages.error(request,'Failed to send message. Try Again!')
        return redirect('home')

    popular_food=Food.objects.filter(is_popular=True)
    special_food=Food.objects.get(is_special=True)
    if request.user.is_authenticated:
        cart_size=len(Items.objects.filter(user=request.user))
    else:
        cart_size=0
    print(123)
    return render(request,'Home/index.html',{'cart_size':cart_size,'popular':popular_food,'special':special_food})

def Menu(request):
    if request.method=="POST":
        search=request.POST.get('search')
        search=str(search)
        result=[]
        food=Food.objects.all()
        for f in food:
            if search.upper() in f.name.upper():
                result.append(f)
        if request.user.is_authenticated:
            cart_size=len(Items.objects.filter(user=request.user))
        else:
            cart_size=0
        return render(request,'Home/menu.html',{'cart_size':cart_size,'result':result,'search':True})
    main_course,sandwich,salads,maggi=[],[],[],[]
    dishes=Food.objects.all()
    for dish in dishes:
        if dish.category.name == "Main Course":
            main_course.append(dish)
        elif dish.category.name == "Sandwich":
            sandwich.append(dish)
        elif dish.category.name == "Salads":
            salads.append(dish)
        else:
            maggi.append(dish)
    if request.user.is_authenticated:
        cart_size=len(Items.objects.filter(user=request.user))
    else:
        cart_size=0
    return render(request,'Home/menu.html',{'cart_size':cart_size,'main_course':main_course,'sandwich':sandwich,'salads':salads,
    'maggi':maggi,'search':False})

@deco_auth
def Cart(request):
    items=Items.objects.filter(user=request.user)
    cost=Cost(items)
    return render(request,'Home/cart.html',{'cart_size':len(items),'cart':items,'cost':cost,'size':len(items),'iscart':'yes'})

@deco_auth
def Add_item(request):
    id=request.GET.get('id')
    food=Food.objects.get(id=id)
    try:
        qty=int(request.GET.get('quantity'))
        if qty == 0:
            messages.warning(request,"Quantity cannot be 0. Try Again!")
            return redirect('home')
        item=isexist(food,request)
        if item == None:
            cart=Items.objects.create(food=food,user=request.user,qty=qty)
            cart.save()
        else:
            combine(item,food,qty)
    except:
        item=isexist(food,request)
        if item == None:
            cart=Items.objects.create(food=food,user=request.user,qty=1)
            cart.save()
        else:
            combine(item,food,1)
    messages.success(request,'Item successfully added to the cart')
    return redirect('home')

def Cost(items):
    total=0
    for item in items:
        total+=item.food.price*item.qty
    return total

@deco_auth
def Remove_Item(request):
    Items.objects.filter(id=request.GET.get('id')).delete()
    messages.success(request,'Item successfully removed from the cart')
    if len(Items.objects.filter(user=request.user)) == 0:
        return redirect('home')
    else:
        return redirect('cart')

def Order_Food(request):
    id=request.GET.get('id')
    food=Food.objects.get(id=id)
    if request.user.is_authenticated:
        cart_size=len(Items.objects.filter(user=request.user))
    else:
        cart_size=0
    return render(request,'Home/order.html',{'cart_size':cart_size,'food':food,'iscart':'no'})

@deco_auth
def Summary(request):  
    if request.method == "POST":
        
        price=int(request.POST.get('price'))
        try:
            price=int(price)*int(request.GET.get('quantity'))
        except:
            pass
        price*=100
        iscart=request.POST.get('iscart')
        if iscart == "no":
            id=int(request.POST.get('id'))
        address=request.POST.get('address')
        phone=request.POST.get('phone')
        name=request.POST.get('name')
        client=razorpay.Client(auth=("rzp_live_eIfhzql8SVrMhC","fkX5mwIscLwl4rKQhQ5OD53L"))
        payment = client.order.create({'amount':price,'currency':'INR','payment_capture':'1'})
        order= Order.objects.create(user=request.user,address=address,name=name,phone=phone,razorpay_payment_id=payment['id'])
        if iscart == "yes":
            cart=Items.objects.filter(user=request.user)
            for item in cart:
                order.dish.add(item)
        else:
            food=Food.objects.get(id=id)
            cart=Cart()
            cart.food=food
            cart.user=request.user
            cart.quantity=request.POST.get('qty')
            order.dish.add(cart)
        if request.POST.get('later'):
            order.pay_on_delivery=True
        order.save()
        if request.POST.get('later'):
            order.paid=True
            order.save()
            return redirect('success')
        else:
            return render(request,"Home/summary.html",{'payment': payment,'name':name,'phone':phone,'email':request.user.email,'address':address,'price':price/100})
    price=int(request.GET.get('price'))
    try:
        qty=int(request.GET.get('quantity'))
    except:
        qty=1
    price=price*qty
    id=request.GET.get('id')
    if request.user.is_authenticated:
        cart_size=len(Items.objects.filter(user=request.user))
    else:
        cart_size=0
    return render(request,'Home/summary.html',{'cart_size':cart_size,'price':price,'iscart':request.GET.get('iscart'),'id':id,'qty':qty})

@csrf_exempt
def Success(request):
    if request.method == "POST":
        a =  (request.POST)
        order_id = ""
        for key , val in a.items():
            print(key,val)
            if key == "razorpay_order_id":
                order_id = val
                break
    
        user = Order.objects.filter(razorpay_payment_id = order_id).first()
        user.paid = True
        user.save()
        messages.success(request,'Your Order Successfully Placed')
    return redirect("home")

@deco_auth
def My_Orders(request):
    my_orders=Order.objects.filter(user=request.user)
    my_orders=[o for o in my_orders if o.paid==True]
    return render(request,'Home/my_orders.html',{'cart':my_orders})

@deco_auth
def Customer_Orders(request):
    if request.user.is_staff == True:
        filter=request.GET.get('filter')
        if filter=="pending":
            orders=Order.objects.filter(paid=True,order_received=False,shipped=False)
        elif filter=='shipped':
            orders=Order.objects.filter(shipped=True,order_received=False)
        elif filter=='completed':
            orders=Order.objects.filter(order_received=True)
        else:
            orders=Order.objects.all()
        orders=[o for o in orders if o.paid==True]
        if request.user.is_authenticated:
            cart_size=len(Items.objects.filter(user=request.user))
        else:
            cart_size=0
        return render(request,'Home/all_orders.html',{'cart_size':cart_size,'cart':orders})
    else:
        redirect('home')

def Order_Shipped(request):
    id=request.GET.get('id')
    order=Order.objects.get(id=id)
    order.shipped=True
    order.save()
    return redirect('customer-orders')

def Order_Completed(request):
    id=request.GET.get('id')
    order=Order.objects.get(id=id)
    order.order_received=True
    order.save()
    return redirect('customer-orders')

def isexist(food,request):
    item=Items.objects.filter(user=request.user,food=food).first()
    return item

def combine(item,food,qty):
    cost=food.price*qty
    item.qty+=qty
    item.food.price+=cost
    item.save()

def Plus(request):
    id=request.GET.get('id')
    item=Items.objects.get(id=id)
    item.qty+=1
    item.save()
    return redirect('cart')

def Minus(request):
    id=request.GET.get('id')
    item=Items.objects.get(id=id)
    item.qty-=1
    if item.qty==0:
        Items.objects.filter(id=id).delete()
        messages.success(request,'Item successfully removed from the cart')
    else:
        item.save()
    if len(Items.objects.filter(user=request.user)) == 0:
        return redirect('home')
    else:
        return redirect('cart')